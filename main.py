#! venv/bin/python3
from dotenv import load_dotenv
import numpy
import pandas
import uvicorn
from fastapi import FastAPI
import os
import logging
from fastapi import Request
import threading

from pytick.bot.discordbot import BotConfig, DiscordBot
from pytick.query import query
from pytick.scheduler.scheduler import Scheduler
from pytick.utility.utility import get_logger, read_config, save_config
import pytick.dataframe.dataframe as dataframe
import pytick.dataframe.notification as notification

app = FastAPI()
logger = get_logger(__file__, logging.DEBUG)
load_dotenv()

config = os.environ.get("CONFIG_FILE")
users_config_path = os.environ.get("CONFIG_USERS")
app_config = read_config(file_path=config)
tickers = app_config.get('indexes', []).get('nifty50', [])
indicators = app_config.get('indicators', {})
cron_schedules = app_config.get('cron_schedules', {})
cron_notification = app_config.get('cron_notification', {})
tz = app_config.get('tz', 'Asia/Kolkata')
data_handler = dataframe.DataFrameHandler(tz=tz, indicators=indicators)
notification_handler = notification.NotificationHandler(tz=tz)
gherkin_handler = query.QueryHandler(data_handler=data_handler, interval_translation={v: k for k, v in app_config.get('interval_translation', {}).items()})

def save_users(key:str, data):
    save_config(key, data, users_config_path)
bot_config = BotConfig(
    token=os.getenv('DISCORD_BOT_TOKEN'), 
    command_prefix='/', 
    query_handler=gherkin_handler, 
    notification_handler=notification_handler,
    llm_convert_msg=app_config.get('discord_llm_msg', ''), 
    tz=tz,
    schedules=cron_schedules, 
    users_config_path=users_config_path, 
    update_users_callback=save_users,
    zerodha_df=pandas.read_csv(app_config.get("zerodha_instrument_tokens_path", "")),
    trading_view_url=app_config.get('trading_view_url', ''),
    zerodha_url=app_config.get('zerodha_url', ''),
    link_type=app_config.get('link_type', 'zerodha')
)
discord_bot = DiscordBot(config=bot_config)

@app.get("/")
async def read_root():
    return {"info": "This is a FastAPI application which fetches data from "
    "yahoo finance computes indicator values and stores them in influx db."}

@app.get("/df/{ticker}/{interval}")
async def to_dataframe(ticker: str, interval: str):
    result = data_handler.get_tables(tickers=[ticker], interval=interval)
    if result['success'] and ticker in result['data']:
        df = result['data'][ticker]
        df = df.replace({numpy.nan: None})
        return {"success": True, "ticker": ticker, "interval": interval,
            "data": df.to_dict(orient='records')}
    else:
        return {"success": False, "message": f"No data found for ticker {ticker} at interval {interval}"}

@app.get("/notification/{ticker}")
async def notification(ticker: str):
    result = notification_handler.get_corporate_actions(tickers=[ticker])
    if result['success'] and ticker in result['data']:
        df = result['data'][ticker]
        return {"success": True, "ticker": ticker,
            "data": df.to_dict(orient='records')}
    else:
        return {"success": False, "message": f"No data found for ticker {ticker} notifications"}

@app.post("/gherkin")
async def parse_gherkin_query(request: Request):
    jsn = await request.json()
    gherkin_text = jsn.get("gherkin", "")
    if not gherkin_text:
        return {"success": False, "errors": "No Gherkin text provided"}
    is_valid, step_data, errors, df = gherkin_handler.get_gherkin_result(gherkin_str=gherkin_text)
    if not is_valid:
        return {"success": False, "errors": errors}
    return {"success": True, "tickers": step_data, "data": df.to_dict(orient='records')}

if __name__ == "__main__":
    # start scheduler
    scheduler = Scheduler(tz)
    scheduler.start()
    
    # Schedule ohlc fetching jobs
    for interval, params in cron_schedules.items():
        data_handler.set_tables(tickers=tickers, interval=interval)
        scheduler.add_periodic_job(func=lambda tickers=tickers, interval=interval: data_handler.set_tables(tickers=tickers, interval=interval), params=params, job_id=f"yf_job_{interval}")
    # Schedule corporate actions fetching job in 5 minutes interval
    notification_handler.set_corporate_actions(tickers=tickers)
    scheduler.add_periodic_job(func=lambda tickers=tickers: notification_handler.set_corporate_actions(tickers=tickers), 
                               params=cron_notification, job_id="corp_actions_job")

    # Start Discord bot in a background thread so it doesn't block the main thread/uvicorn
    def _run_discord():
        try:
            discord_bot.run()
        except Exception:
            logger.exception("Discord bot stopped with an exception")

    discord_thread = threading.Thread(target=_run_discord, name="discord-bot-thread", daemon=True)
    discord_thread.start()
    
    # Run the FastAPI app using uvicorn. When uvicorn exits, we'll stop the scheduler.
    try:
        uvicorn.run(app, host="localhost", port=8000)
    finally:
        # ensure scheduler stops on shutdown
        try:
            # i=1
            scheduler.stop()
        except Exception:
            logger.exception("Error stopping scheduler")
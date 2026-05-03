from dotenv import load_dotenv
import numpy
import pandas
import asyncio
import redis
import uvicorn
from fastapi import FastAPI, HTTPException
import os
import logging
from fastapi import Request
import threading
import copy
from func_timeout import func_timeout, FunctionTimedOut

from pytick.bot.discordbot import BotConfig, DiscordBot
from pytick.llm.prompt import generate_prompt
from pytick.query import query
from pytick.query.trade import TradeHandler
from pytick.scheduler.scheduler import Scheduler
from pytick.utility.convo_store import ConvoStore
from pytick.utility.utility import get_logger, read_config, read_file
import pytick.dataframe.dataframe as dataframe
import pytick.dataframe.notification as notification

app = FastAPI()

logger = get_logger(__file__, logging.DEBUG)
load_dotenv()

config = os.environ.get("CONFIG_FILE")
app_config = read_config(file_path=config)
tickers = list(set(app_config.get('indexes', {}).get('nifty50', []))
               | set(app_config.get('indexes', {}).get('nifty100', [])))
indicators = app_config.get('indicators', {})
cron_schedules = app_config.get('cron_schedules', {})
cron_notification = app_config.get('cron_notification', {})
tz = app_config.get('tz', 'Asia/Kolkata')
convo_store = ConvoStore(redis.from_url(
    os.getenv('REDIS_URL', 'redis://localhost:6379/0'), encoding="utf-8", decode_responses=True))
data_handler = dataframe.DataFrameHandler(tz=tz, indicators=indicators)
notification_handler = notification.NotificationHandler(
    tz=tz, max_rows=1000, app_data_path=app_config.get('app_data_path', ''))
gherkin_handler = query.QueryHandler(data_handler=data_handler,
                                     notification_handler=notification_handler,
                                     interval_translation={v: k for k, v in app_config.get(
                                         'interval_translation', {}).items()},
                                     interval_seconds=app_config.get('interval_seconds', {}))
generate_prompt(config=app_config,
                output_init_prompt=os.path.join(app_config.get(
                    'app_data_path', ''), "llm_prompt_init.prompt.md"),
                output_retry_prompt=os.path.join(app_config.get(
                    'app_data_path', ''), "llm_prompt_retry.prompt.md"),
                output_getting_started=os.path.join(app_config.get(
                    'app_data_path', ''), "getting_started.md"),
                )

bot_config = BotConfig(
    token=os.getenv('DISCORD_BOT_TOKEN', ''),
    command_prefix='/',
    query_handler=gherkin_handler,
    notification_handler=notification_handler,
    llm_convert_msg=app_config.get('discord_llm_msg', ''),
    tz=tz,
    schedules=cron_schedules,
    zerodha_df=pandas.read_csv(app_config.get(
        "zerodha_instrument_tokens_path", "")),
    trading_view_url=app_config.get('trading_view_url', ''),
    zerodha_url=app_config.get('zerodha_url', ''),
    link_type=app_config.get('link_type', 'zerodha'),
    backtest_iterations=app_config.get('backtest_iterations', 10),
    default_ticker=app_config.get('default_ticker', 'SBIN'),
    convo_store=convo_store,
    convo_ttl_seconds=int(os.getenv('CONVO_TTL_SECONDS', '900')),
    guild_id=int(os.getenv('DISCORD_GUILD_ID', '0')),
    modal_timeout=120,
    llm_timeout=60,
    ollama_model='gemma3',
    openai_model='gpt-5.4',
    llm_prompt=read_file(file_path=os.path.join(app_config.get(
        'app_data_path', ''), "llm_prompt_init.prompt.md")),
    retry_prompt=read_file(file_path=os.path.join(app_config.get(
        'app_data_path', ''), "llm_prompt_retry.prompt.md")),
    joining_prompt=read_file(file_path=os.path.join(app_config.get(
        'app_data_path', ''), "getting_started.md")),
    disclaimer=read_file(file_path=os.path.join(app_config.get(
        'app_data_path', ''), "disclaimer.md"))
)
discord_bot = DiscordBot(config=bot_config)


@app.get("/")
async def read_root():
    return {"info": "This is a FastAPI application which fetches data from "
            "yahoo finance computes indicator values and replies to client query in discord."}


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
async def get_notification(ticker: str):
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
    is_valid, step_data, errors, df = gherkin_handler.get_gherkin_result(
        gherkin_str=gherkin_text)
    if not is_valid:
        return {"success": False, "errors": errors}
    return {"success": True, "tickers": step_data, "data": df.to_dict(orient='records')}

@app.post("/backtest")
async def backtest_gherkin_query(request: Request):
    try:
        jsn = await request.json()
        gherkin_text = jsn.get("gherkin", "")
        start = jsn.get('start', 20)
        stop = jsn.get('stop', 0)
        stop_loss = jsn.get('stop_loss', 1)
        commision = jsn.get('commision', 0.01)

        if not gherkin_text:
            return {"success": False, "errors": "No Gherkin text provided"}

        trade_handler = TradeHandler()
        errors = []
        # Define the core logic as an internal async function
        async def backtest_func():
            for itr in range(start, stop, -1):
                # 1. Check if the client cancelled the request
                if await request.is_disconnected():
                    print("!!! Client disconnected. Stopping server-side task. !!!")
                    return None
                
                # 2. Run your backtest logic
                # If get_backtest_result is a heavy CPU-bound (sync) function,
                # wrap it in run_in_executor to avoid freezing the server.
                try:
                    bt_query_handler = copy.deepcopy(gherkin_handler)
                    
                    # Using run_in_executor allows the event loop to keep heartbeating
                    # so 'is_disconnected()' actually stays responsive.
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(
                        None, 
                        bt_query_handler.get_backtest_result,
                        gherkin_text, trade_handler, itr, stop_loss
                    )
                except Exception as e:
                    errors.append(str(e))
            
            return {"status": "success"}

        try:
            # 3. Apply the timeout (e.g., 10 hours)
            # This replaces func_timeout with an async-friendly version
            timeout_seconds = 10 * 60 * 60
            result = await asyncio.wait_for(backtest_func(), timeout=timeout_seconds)
            
            if result is None: # Handled disconnection
                return {"detail": "Cancelled"}
            # return result

        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail='Timeout')

        r_multiples = trade_handler.close_df['rmulti'] - commision
        
        # 2. Calculate Fitness Metrics for the AI Agent
        metrics = {
            "total_trades": len(r_multiples),
            "r": r_multiples,
            "expectancy_r": r_multiples.mean() if not r_multiples.empty else 0,
            "std_dev_r": r_multiples.std() if not r_multiples.empty else 0,
            "max_r": r_multiples.max() if not r_multiples.empty else 0,
            "min_r": r_multiples.min() if not r_multiples.empty else 0,
            "win_rate": (r_multiples > 0).sum() / len(r_multiples) if len(r_multiples) > 0 else 0
        }
        # SQN > 1.6: Average, 2.0: Good, 3.0: Excellent, 5.0+: Holy Grail
        metrics["sqn"] = (numpy.sqrt(metrics["total_trades"]) * 
                  (metrics["expectancy_r"] / (metrics["std_dev_r"] + 1e-6)))

        return {
            "status": "success",
            "metrics": {k: round(v, 2) if isinstance(v, (int, float, numpy.number)) else v 
                        for k, v in metrics.items()},
            "data": {
                "trades": trade_handler.close_df.to_dict(orient='records'),
                "errors": errors
            }
        }
    except FunctionTimedOut as e:
        return {
            "status": "timeout",
            "data": {
                "errors": e.args
            }
        }
    except Exception as e:
        return {
            "status": "failed",
            "data": {
                "errors": e.args
            }
        }

# Health check endpoint for Docker Compose
@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Run FastAPI app with custom port")
    parser.add_argument('--port', type=int, default=int(os.getenv("APP_PORT", 8000)),
                        help='Port to run the server on')
    args = parser.parse_args()

    # start scheduler
    scheduler = Scheduler(tz)
    scheduler.start()

    # Schedule ohlc fetching jobs
    for interval, params in cron_schedules.items():
        data_handler.set_tables(tickers=tickers, interval=interval)
        scheduler.add_periodic_job(func=lambda tickers=tickers,
                                   interval=interval: data_handler.set_tables(tickers=tickers, interval=interval),
                                   params=params, job_id=f"yf_job_{interval}")
    # Schedule corporate actions fetching job in 5 minutes interval
    notification_handler.set_corporate_actions(tickers=tickers)
    scheduler.add_periodic_job(func=lambda tickers=tickers: notification_handler.set_corporate_actions(tickers=tickers),
                               params=cron_notification, job_id="corp_actions_job")

    # Start Discord bot in a background thread so it doesn't block the main thread/uvicorn
    def _start_discord():
        try:
            asyncio.run(discord_bot.run_async())
        except Exception:
            logger.exception("Discord bot stopped with an exception")

    discord_thread = threading.Thread(
        target=_start_discord, name="discord-bot-thread", daemon=True)
    discord_thread.start()

    # Run the FastAPI app using uvicorn. When uvicorn exits, we'll stop the scheduler.
    try:
        uvicorn.run(app, host="localhost", port=args.port, access_log=False)
    finally:
        # ensure scheduler stops on shutdown
        try:
            scheduler.stop()
            pass
        except Exception:
            logger.exception("Exception stopping scheduler")

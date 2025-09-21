#! venv/bin/python3
from dotenv import load_dotenv
import uvicorn
from fastapi import FastAPI
import os
from utility import read_config
import logging
from scheduler import Scheduler

from utility import get_logger
import dataframe

app = FastAPI()
logger = get_logger(__file__, logging.DEBUG)
load_dotenv()

config = os.environ.get("CONFIG_FILE_DEBUG")
tickers = read_config(config).get('indexes', []).get('nifty50', [])
indicators = read_config(config).get('indicators', {})
cron_schedules = read_config(config).get('cron_schedules', {})
tz = read_config(config).get('tz', 'Asia/Kolkata')
data_handler = dataframe.DataFrameHandler(tz=tz, indicators=indicators)

@app.get("/")
async def read_root():
    return {"info": "This is a FastAPI application which fetches data from "
    "yahoo finance computes indicator values and stores them in influx db."}

@app.get("/df/{ticker}/{interval}")
async def to_dataframe(ticker: str, interval: str):
    result = data_handler.get_tables(tickers=[ticker], interval=interval)
    if result['success'] and ticker in result['data']:
        df = result['data'][ticker]
        return {"success": True, "ticker": ticker, "interval": interval,
            "data": df.to_dict(orient='records')}
    else:
        return {"success": False, "message": f"No data found for ticker {ticker} at interval {interval}"}

if __name__ == "__main__":   
    scheduler = Scheduler(tz)
    scheduler.start()
    for interval, params in cron_schedules.items():
        data_handler.set_tables(tickers=tickers, interval=interval)
        scheduler.add_periodic_job(func=lambda tickers=tickers, interval=interval: data_handler.set_tables(tickers=tickers, interval=interval), params=params, job_id=f"yf_job_{interval}")

    uvicorn.run(app, host="localhost", port=8000)

    scheduler.stop()
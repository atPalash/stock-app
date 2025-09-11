#! venv/bin/python3
from dotenv import load_dotenv
import numpy as np
import pandas as pd
import uvicorn
from fastapi import FastAPI
import os
from utility import read_config
import logging

from scheduler import Scheduler
from influx import InfluxDBHandler
from yf import download_stock_data
from utility import get_logger, normalize_index_to_tz

app = FastAPI()
logger = get_logger('main', logging.DEBUG)
load_dotenv()

config = os.environ.get("CONFIG_FILE_DEBUG")
token = os.environ.get("INFLUX_TOKEN")
org = os.environ.get("INFLUX_ORG")
url = os.environ.get("INFLUX_URL")
tickers = read_config(config).get('indexes', []).get('nifty50', [])
tz = read_config(config).get('tz', 'Asia/Kolkata')
bucket = os.environ.get("INFLUX_BUCKET")
influx_handler = InfluxDBHandler(tz, url, token, org, bucket, prefix="stock_data")

@app.get("/")
async def read_root():
    return {"info": "This is a FastAPI application which fetches data from "
    "yahoo finance computes indicator values and stores them in influx db."}

@app.get("/df/{ticker}/{interval}")
async def to_dataframe(ticker: str, interval: str):
    df = influx_handler.to_dataframe(interval=interval, ticker=ticker)
    df = df.replace({np.nan: None})
    df = df.reset_index()
    return {"info":"get data as pandas df","ticker": ticker, "interval": interval, 
            "data": df.to_dict(orient='records')}
@app.get("/clear")
async def read_item():
    return {"message": "clear"}
 
if __name__ == "__main__":
    influx_handler.clear()
    # if not influx_handler.get_tables().empty:
    #     logger.error(f"InfluxDB has older data")
    #     exit(1)

    def yf_job(interval: str)->None:
        logger.info(f"Downloading data for interval {interval}")
        for ticker in tickers:    
            previous_data = influx_handler.to_dataframe(interval=interval, ticker=ticker)
            data = download_stock_data(ticker=ticker, interval=interval, tz=tz)

            # Normalize both to tz-aware utility
            previous_data = normalize_index_to_tz(previous_data, tz)
            data = normalize_index_to_tz(data, tz)

            # Concatenate so new data is last
            combined_data = pd.concat([previous_data, data])
            combined_data = combined_data[~combined_data.index.duplicated(keep='first')]
            influx_handler.write(data=combined_data, ticker=ticker, interval=interval, config=config)

    cron_schedules = read_config(config).get('cron_schedules', {})
    scheduler = Scheduler(tz)
    scheduler.start()
    for interval, params in cron_schedules.items():
        yf_job(interval=interval)
        scheduler.add_periodic_job(func=lambda interval=interval: yf_job(interval=interval), params=params, job_id=f"yf_job_{interval}")

    uvicorn.run(app, host="localhost", port=8000)
    influx_handler.close()
    scheduler.stop()
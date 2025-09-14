#! venv/bin/python3
from dotenv import load_dotenv
import numpy as np
import pandas as pd
import uvicorn
from fastapi import FastAPI
import os
from utility import read_config
import logging
import concurrent.futures

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
    # We'll clear data per ticker/interval before writing, so no need for a global clear
    # Ensure bucket exists
    influx_handler.create_bucket_if_not_exists()

    def process_ticker(ticker: str, interval: str)->None:
        try:
            # Download fresh data directly from source first
            data = download_stock_data(ticker=ticker, interval=interval, tz=tz)
            
            # Normalize to tz-aware
            data = normalize_index_to_tz(data, tz)
            
            if data.empty:
                logger.warning(f"Received empty data for {ticker} at interval {interval}, skipping update")
                return
            
            # Use the atomic replace method to minimize data unavailability window
            success = influx_handler.replace_data(data=data, ticker=ticker, interval=interval, config=config)
            
            if not success:
                logger.error(f"Failed to update data for {ticker} at interval {interval}")
            return success
        
        except Exception as e:
            logger.error(f"Error processing {ticker} at interval {interval}: {e}")
    
    def yf_job(interval: str)->None:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        # Use a ThreadPoolExecutor as this is primarily I/O bound
        max_workers = min(10, len(tickers))  # Limit number of threads
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks to the executor and map them to their tickers for error reporting
            future_to_ticker = {executor.submit(process_ticker, ticker, interval): ticker for ticker in tickers}
            
            # Process results as they complete and handle exceptions
            for future in as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                try:
                    # Get the result (or exception) from the future
                    future.result()
                except Exception as e:
                    # Log any exceptions that weren't caught in process_ticker
                    logger.error(f"Uncaught exception in process_ticker for {ticker} at {interval}: {e}")

    cron_schedules = read_config(config).get('cron_schedules', {})
    scheduler = Scheduler(tz)
    scheduler.start()
    for interval, params in cron_schedules.items():
        yf_job(interval=interval)
        scheduler.add_periodic_job(func=lambda interval=interval: yf_job(interval=interval), params=params, job_id=f"yf_job_{interval}")

    uvicorn.run(app, host="localhost", port=8000)
    influx_handler.close()
    scheduler.stop()
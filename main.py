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
import multiprocessing
from functools import partial

from scheduler import Scheduler
from influx import InfluxDBHandler
from yf import download_stock_data
from utility import get_logger, normalize_index_to_tz
import yf

app = FastAPI()
logger = get_logger('main', logging.DEBUG)
load_dotenv()

config = os.environ.get("CONFIG_FILE_DEBUG")
token = os.environ.get("INFLUX_TOKEN")
org = os.environ.get("INFLUX_ORG")
url = os.environ.get("INFLUX_URL")
tickers = read_config(config).get('indexes', []).get('nifty50', [])
indicators = read_config(config).get('indicators', {})
cron_schedules = read_config(config).get('cron_schedules', {})
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
 
# Define a function that can be pickled for multiprocessing
def mp_process_ticker(data, ticker, interval, tz_str, url_str, token_str, org_str, bucket_str):
    try:
        # Create a process-specific logger
        process_logger = get_logger(f'process_{ticker}', logging.DEBUG)
        
        # Create a new InfluxDB handler for this process
        local_influx = InfluxDBHandler(tz_str, url_str, token_str, org_str, bucket_str, prefix="stock_data")
                
        # Normalize to tz-aware
        data = normalize_index_to_tz(data, tz_str)
        if data.empty:
            process_logger.warning(f"Received empty data for {ticker} at {interval}, skipping update")
            return False
        
        # Use the atomic replace method to minimize data unavailability window
        success = local_influx.replace_data(data=data, ticker=ticker, interval=interval)
        
        # Close the connection when done
        local_influx.close()
        
        if not success:
            process_logger.error(f"Failed to update data for {ticker} at {interval}")
        return success
    except Exception as e:
        print(f"Error processing ticker {ticker} at interval {interval}: {e}")
        return False

if __name__ == "__main__":
    # We'll clear data per ticker/interval before writing, so no need for a global clear
    # Ensure bucket exists
    influx_handler.drop_influxdb_bucket()
    influx_handler.create_bucket_if_not_exists()
    
    def yf_job(interval: str)->None:
        data = yf.get_tickers_table(tickers=tickers, interval=interval, tz=tz, indicators=indicators)
        # Create a pool of processes (one for each CPU core)
        num_processes = min(multiprocessing.cpu_count(), len(tickers))
        # Prepare the parameters for each process
        process_args = [
            (data[ticker], ticker, interval, tz, url, token, org, bucket) 
            for ticker in tickers
        ]
        
        # Use a process pool executor for true parallelism
        with multiprocessing.Pool(processes=num_processes) as pool:
            # Map the processing function to all tickers with their parameters
            pool.starmap(mp_process_ticker, process_args)

    scheduler = Scheduler(tz)
    scheduler.start()
    for interval, params in cron_schedules.items():
        yf_job(interval=interval)
        scheduler.add_periodic_job(func=lambda interval=interval: yf_job(interval=interval), params=params, job_id=f"yf_job_{interval}")

    uvicorn.run(app, host="localhost", port=8000)
    influx_handler.close()
    scheduler.stop()
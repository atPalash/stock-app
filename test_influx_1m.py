import os
import pandas as pd
from influx import InfluxDBHandler
import yf
from dotenv import load_dotenv

def test_yf_vs_influx_datetime():
    load_dotenv()
    config = os.environ.get("CONFIG_FILE_DEBUG")
    token = os.environ.get("INFLUX_TOKEN")
    org = os.environ.get("INFLUX_ORG")
    url = os.environ.get("INFLUX_URL")
    bucket = os.environ.get("INFLUX_BUCKET")
    interval = "1m"
    ticker = "TCS"

    influx_handler = InfluxDBHandler(url, token, org, bucket, prefix="stock_data")
    # Download fresh data from Yahoo Finance
    yf_data = yf.download_stock_data(ticker, interval=interval)
    # Get data from InfluxDB
    influx_df = influx_handler.to_dataframe(interval=interval, ticker=ticker)

    # Compare datetime indices
    yf_datetimes = set(pd.to_datetime(yf_data.index))
    influx_datetimes = set(pd.to_datetime(influx_df.index))
    missing_in_influx = yf_datetimes - influx_datetimes
    # missing_in_yf = influx_datetimes - yf_datetimes

    # print(f"Missing in InfluxDB: {missing_in_influx}")
    # print(f"Missing in Yahoo Finance: {missing_in_yf}")
    assert len(missing_in_influx) == 0, "Some Yahoo Finance datetimes are missing in InfluxDB!"
    # assert len(missing_in_yf) == 0, "Some InfluxDB datetimes are missing in Yahoo Finance!"

if __name__ == "__main__":
    test_yf_vs_influx_datetime()

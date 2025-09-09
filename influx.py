import os, time
import warnings
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import warnings
from influxdb_client.client.warnings import MissingPivotFunction
from dotenv import load_dotenv
import os
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timezone

from utility import read_config
import yf


class InfluxDBHandler:
    def __init__(self, url, token, org, bucket, prefix="stock_data"):
        self.client = InfluxDBClient(url=url, token=token, org=org)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.bucket = bucket
        self.org = org
        self.point_name = f"{prefix}"

    def to_dataframe(self, interval:str, ticker:str) -> pd.DataFrame:
        query = f'''
        from(bucket: "{self.bucket}")
                    |> range(start: 0)
                    |> filter(fn: (r) => r._measurement == "{self.point_name}" and r.ticker == "{ticker}" and r.interval == "{interval}")
                    |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        '''
        df = self.client.query_api().query_data_frame(org=self.org, query=query)
        # Drop influx columns except OHLC, indicators, and _time
        drop_cols = [col for col in df.columns if col.startswith('_') and col != '_time'] + ['result', 'table', 'ticker', 'interval']
        df = df.drop(columns=drop_cols, errors='ignore')
        # Rename _time to Datetime and set as DatetimeIndex
        if '_time' in df.columns:
            dt = pd.to_datetime(df['_time'])
            # Remove timezone info if present
            if hasattr(dt.dt, 'tz') and dt.dt.tz is not None:
                dt = dt.dt.tz_localize(None)
            df['Datetime'] = dt
            df = df.drop(columns=['_time'])
            df = df.set_index('Datetime')
        return df

    def get_tables(self) -> pd.DataFrame:
        warnings.simplefilter("ignore", MissingPivotFunction)
        query = f'''
        import "influxdata/influxdb/schema"
        schema.measurements(bucket: "{self.bucket}") 
        '''
        measurements = self.client.query_api().query_data_frame(org=self.org, query=query)
        return measurements
    
    def close(self):
        self.client.close()

    def write(self, data:pd.DataFrame, ticker:str, interval:str, config:str):
        points = [] # List to hold multiple points for batch writing
        df, indicator_col_prefixes = self.__calculate_indicators(data, config)
        for index, row in df.iterrows():
            point = (
                Point(self.point_name)
                .tag("ticker", ticker)
                .tag("interval", interval)
                .field("Open", float(row["Open"]))
                .field("High", float(row["High"]))
                .field("Low", float(row["Low"]))
                .field("Close", float(row["Close"]))
                .field("Volume", int(row["Volume"]))
                .field("Dividends", int(row["Dividends"]))
                .field("Stock Splits", int(row["Stock Splits"]))
                .time(index, WritePrecision.S)
            )
            # Add all indicator fields
            for col in df.columns:
                if col.lower().startswith(indicator_col_prefixes) and not pd.isna(row[col]):
                    point.field(col, float(row[col]))
            points.append(point)
        self.write_api.write(bucket=self.bucket, org=self.org, record=points)

    def clear(self):
        # Define time range to delete all data
        start = "1970-01-01T00:00:00Z"
        stop = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Delete all data in the bucket
        self.client.delete_api().delete(start=start, stop=stop, predicate='', bucket=self.bucket, org=self.org)

    def __calculate_indicators(self, df: pd.DataFrame, config:str) -> tuple[pd.DataFrame, tuple]:
        indicator_col_prefixes = ('sma_', 'ema_') # should match the prefixes used ind_type == 'SMA'/'EMA' etc
        indicators = read_config(config).get('indicators', {})
        for ind_type, ind_conf in indicators.items():
            periods = ind_conf.get('periods', [])
            sources = ind_conf.get('sources', [])
            for src in sources:
                src_col = src.lower() if src.lower() in df.columns else src.capitalize()
                for period in periods:
                    col_name = f"{ind_type}_{period}_{src}"
                    if ind_type == 'sma':
                        df[col_name] = ta.sma(df[src_col], length=period).round(2)
                    elif ind_type == 'ema':
                        df[col_name] = ta.ema(df[src_col], length=period).round(2)
        return df, indicator_col_prefixes

if __name__ == "__main__":
    # Load the .env file
    load_dotenv()

    config = os.environ.get("CONFIG_FILE_DEBUG")
    token = os.environ.get("INFLUX_TOKEN")
    org = os.environ.get("INFLUX_ORG")
    url = os.environ.get("INFLUX_URL")
    intervals = read_config(config).get('intervals', [])
    tickers = read_config(config).get('indexes', []).get('nifty50', [])
    bucket=os.environ.get("INFLUX_BUCKET")
    influx_handler = InfluxDBHandler(url, token, org, bucket, prefix="stock_data")

    # influx_handler.clear()

    # for interval in intervals:
    #     for ticker in tickers:
    #         data = yf.download_stock_data(ticker, interval=interval)
    #         influx_handler.write(data, ticker, interval, config)
    #         time.sleep(1)  # Sleep to avoid hitting rate limits
    # print(influx_handler.get_tables())
    df = influx_handler.to_dataframe(interval="1m", ticker="BEL")
    print(df)
    influx_handler.close()

# '''
# # for interval in intervals:
# #   for ticker in tickers:
# #     data = yf.download_stock_data(ticker, interval=interval)
# # # # Define your Flux query
# # # # query = f'''
# # # # from(bucket: "{bucket}")
# # # #   |> range(start: -30d)
# # # #   |> filter(fn: (r) => r._measurement == "ohlc" and r.symbol == "BEL.NS")
# # # # '''
# # # query = f'''
# # # from(bucket: "{bucket}")
# # #   |> range(start: 0)
# # #   |> filter(fn: (r) => r._measurement == "stock_data" and r.ticker == "BEL.NS")
# # #   |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
# # # '''
# # # # tables = influx_client.query_api().query(org=org, query=query)
# # # # for table in tables:
# # # #     for record in table.records:
# # # #         print(f'{record.values["_time"]}: {record.values["_field"]} = {record.values["_value"]}')

# # # Query data
# # data_frame = influx_client.query_api().query_data_frame(org=org, query=query)
# # if not data_frame.empty:
# #   data_frame['_time'] = pd.to_datetime(data_frame['_time'])
# #   data_frame.set_index('_time', inplace=True)
# #   print(data_frame)
# # else:
# #   print('No data found for BEL.NS in stock_data measurement.')
# # influx_client.close()

# '''

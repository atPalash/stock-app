import os, time
import pytz
import warnings
from influxdb_client import InfluxDBClient, Point, WritePrecision, BucketsApi
from influxdb_client.client.write_api import SYNCHRONOUS
import warnings
from influxdb_client.client.warnings import MissingPivotFunction
from dotenv import load_dotenv
import os
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timezone

import requests

from utility import get_logger, read_config, normalize_index_to_tz
import yf

logger = get_logger(__name__)
class InfluxDBHandler:
    def __init__(self, tz, url, token, org, bucket, prefix="stock_data", max_retries=3, retry_delay=1):
        self.tz = tz
        self.token = token
        self.url = url
        self.bucket = bucket
        self.org = org
        self.point_name = f"{prefix}"
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Initialize with proper error handling
        self._initialize_client()
        
    def _initialize_client(self):
        """Initialize or re-initialize the InfluxDB client connection."""
        try:
            self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            return True
        except Exception as e:
            logger.error(f"Error initializing InfluxDB client: {e}")
            return False
            
    def _ensure_connection(self):
        """
        Ensures the connection to InfluxDB is active.
        Attempts to reconnect if necessary.
        
        Returns:
            bool: True if connection is active, False otherwise
        """
        for attempt in range(self.max_retries):
            try:
                # Check connection by making a simple API call
                self.client.ping()
                return True
            except Exception as e:
                logger.error(f"Connection check failed (attempt {attempt+1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    # Wait before retrying
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                    # Reinitialize client before next attempt
                    self._initialize_client()
                else:
                    logger.error("Max retries exceeded. Could not establish connection.")
        return False
        
    def _with_retry(self, operation_name, operation_func, *args, **kwargs):
        """
        Generic retry mechanism for InfluxDB operations.
        
        Args:
            operation_name: Name of the operation (for logging)
            operation_func: Function to execute with retry
            *args, **kwargs: Arguments to pass to the operation function
            
        Returns:
            The result of the operation function if successful, False otherwise
        """
        for attempt in range(self.max_retries):
            try:
                # First ensure connection is active
                if not self._ensure_connection():
                    logger.error(f"Could not establish connection to InfluxDB for {operation_name} (attempt {attempt+1}/{self.max_retries})")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                    return False
                
                # Execute the operation
                result = operation_func(*args, **kwargs)
                return result
                
            except Exception as e:
                logger.warning(f"Error during {operation_name} (attempt {attempt+1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                    # Reinitialize client before next attempt
                    self._initialize_client()
                else:
                    logger.error(f"Max retries exceeded. Could not complete {operation_name}.")
        
        return False

    def to_dataframe(self, interval:str, ticker:str) -> pd.DataFrame:
        """
        Query InfluxDB for data and convert to DataFrame with retry logic.
        
        Args:
            interval: Time interval (1m, 5m, etc.)
            ticker: Stock ticker symbol
            
        Returns:
            pd.DataFrame: DataFrame with the requested data, empty if no data or error
        """
        query = f'''
        from(bucket: "{self.bucket}")
                    |> range(start: 0)
                    |> filter(fn: (r) => r._measurement == "{self.point_name}" and r.ticker == "{ticker}" and r.interval == "{interval}")
                    |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        '''
        
        def query_operation():
            df = self.client.query_api().query_data_frame(org=self.org, query=query)
            if df is not None and not df.empty:
                # Drop influx columns except OHLC, indicators, and _time
                drop_cols = [col for col in df.columns if col.startswith('_') and col != '_time'] + ['result', 'table', 'ticker', 'interval']
                df = df.drop(columns=drop_cols, errors='ignore')
                # Rename _time to Datetime and set as DatetimeIndex
                if '_time' in df.columns:
                    dt = pd.to_datetime(df['_time'])
                    # Always localize to UTC first, then convert to tz for user-facing results
                    if dt.dt.tz is None:
                        dt = dt.dt.tz_localize('UTC')
                    dt = dt.dt.tz_convert(self.tz)
                    df['Datetime'] = dt
                    df = df.drop(columns=['_time'])
                    df = df.set_index('Datetime')
                df = normalize_index_to_tz(df, self.tz)
            return df
            
        result = self._with_retry(f"querying data for ticker={ticker}, interval={interval}", query_operation)
        if result is False:
            # If retry failed, return empty DataFrame
            return pd.DataFrame()
        return result

    def get_tables(self) -> pd.DataFrame:
        """
        Get available measurements in InfluxDB with retry logic.
        
        Returns:
            pd.DataFrame: DataFrame with available measurements, empty if error
        """
        warnings.simplefilter("ignore", MissingPivotFunction)
        query = f'''
        import "influxdata/influxdb/schema"
        schema.measurements(bucket: "{self.bucket}") 
        '''
        
        def query_operation():
            return self.client.query_api().query_data_frame(org=self.org, query=query)
            
        result = self._with_retry("getting available measurements", query_operation)
        if result is False:
            # If retry failed, return empty DataFrame
            return pd.DataFrame()
        return result
    
    def close(self):
        """Safely close the InfluxDB client connection."""
        try:
            if hasattr(self, 'client'):
                self.client.close()
        except Exception as e:
            logger.error(f"Error closing InfluxDB client connection: {e}")

    def clear(self):
        """
        Clear all data from the bucket with retry logic.
        
        Returns:
            bool: True if successful, False otherwise
        """
        # Define time range to delete all data
        start = "1970-01-01T00:00:00Z"
        stop = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Define the delete operation as a function
        def delete_operation():
            self.client.delete_api().delete(start=start, stop=stop, predicate='', bucket=self.bucket, org=self.org)
            return True
        
        # Execute with retry mechanism
        return self._with_retry(f"clearing all data from bucket {self.bucket}", delete_operation)
        
    def clear_ticker_interval(self, ticker, interval):
        """
        Clear data for a specific ticker and interval with retry logic.
        
        Args:
            ticker: Stock ticker symbol
            interval: Time interval (1m, 5m, etc.)
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Define time range to delete all data for specific ticker and interval
        start = "1970-01-01T00:00:00Z"
        stop = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Create predicate for the specific ticker and interval
        predicate = f'_measurement="{self.point_name}" AND ticker="{ticker}" AND interval="{interval}"'
        
        # Define the delete operation as a function
        def delete_operation():
            self.client.delete_api().delete(start=start, stop=stop, predicate=predicate, bucket=self.bucket, org=self.org)
            return True
        
        # Execute with retry mechanism
        return self._with_retry(f"clearing data for ticker={ticker}, interval={interval}", delete_operation)
        
    def replace_data(self, data, ticker, interval):
        """
        Atomically replace data for a ticker and interval.
        This method first checks if the new data is valid, then performs a clear and write
        operation in the shortest possible time window.
        
        Args:
            data: DataFrame with new data to write
            ticker: Stock ticker symbol
            interval: Time interval (1m, 5m, etc.)
        
        Returns:
            bool: True if replacement was successful, False otherwise
        """
        if data is None or data.empty:
            logger.warning(f"No data to replace for {ticker} at {interval}")
            return False
            
        # First prepare all the points to write
        # df, indicator_col_prefixes = self.__calculate_indicators(data, config)
        # Normalize index to tz before converting to UTC
        df = normalize_index_to_tz(data, self.tz)
        # Ensure index is tz-aware before converting
        if df.index.tz is None:
            idx = df.index.tz_localize('UTC')
        else:
            idx = df.index.tz_convert('UTC')
        
        points = []
        for index, row in zip(idx, df.iterrows()):
            _, row = row
            point = (
                Point(self.point_name)
                .tag("ticker", ticker)
                .tag("interval", interval)
                .time(index, WritePrecision.S)
            )
            # Add all indicator fields
            for col in df.columns:
                if not pd.isna(row[col]):
                    point.field(col, float(row[col]))
            points.append(point)
        
        if not points:
            logger.warning(f"No points to write for {ticker} at {interval}")
            return False
            
        # Define time range to delete all data for specific ticker and interval
        start = "1970-01-01T00:00:00Z"
        stop = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Create predicate for the specific ticker and interval
        predicate = f'_measurement="{self.point_name}" AND ticker="{ticker}" AND interval="{interval}"'
        
        # Define the atomic replace operation as a function that performs both delete and write
        def replace_operation():
            # Delete data matching the predicate
            self.client.delete_api().delete(start=start, stop=stop, predicate=predicate, bucket=self.bucket, org=self.org)
            
            # Immediately write the new points
            result = self.write_api.write(bucket=self.bucket, org=self.org, record=points)
            return True
        
        # Execute with retry mechanism
        return self._with_retry(f"replacing data for {ticker} at {interval}", replace_operation)
        
    def drop_influxdb_bucket(self):
        """
        Drop the InfluxDB bucket with retry logic.
        
        Returns:
            bool: True if successful, False otherwise
        """
        def drop_operation():
            # Get bucket ID
            headers = {
                "Authorization": f"Token {self.token}",
                "Content-Type": "application/json"
            }
            params = {
                "name": self.bucket,
                "org": self.org
            }
            resp = requests.get(f"{self.url}/api/v2/buckets", headers=headers, params=params)
            resp.raise_for_status()
            buckets = resp.json().get("buckets", [])
            if not buckets:
                logger.error("Bucket not found.")
                return True  # Not an error if bucket doesn't exist
                
            bucket_id = buckets[0]["id"]

            # Delete bucket
            del_resp = requests.delete(f"{self.url}/api/v2/buckets/{bucket_id}", headers=headers)
            del_resp.raise_for_status()
            return True
            
        return self._with_retry(f"dropping bucket '{self.bucket}'", drop_operation)
    
    def create_bucket_if_not_exists(self):
        """
        Create the InfluxDB bucket if it doesn't exist with retry logic.
        
        Returns:
            bool: True if successful, False otherwise
        """
        def create_bucket_operation():
            buckets_api = BucketsApi(self.client)
            buckets = buckets_api.find_buckets().buckets
            if not any(b.name == self.bucket for b in buckets):
                buckets_api.create_bucket(bucket_name=self.bucket, org=self.org)
                logger.info(f"Bucket '{self.bucket}' created.")
            else:
                logger.warning(f"Bucket '{self.bucket}' already exists.")
            return True
            
        result = self._with_retry(f"creating bucket '{self.bucket}' if not exists", create_bucket_operation)
        
        # Don't close the client here as it might be used for other operations
        # Only close the client when the InfluxDBHandler instance is no longer needed
        return result

if __name__ == "__main__":
    # Load the .env file
    load_dotenv()

    config = os.environ.get("CONFIG_FILE_DEBUG")
    token = os.environ.get("INFLUX_TOKEN")
    org = os.environ.get("INFLUX_ORG")
    url = os.environ.get("INFLUX_URL")
    intervals = ['2m', '5m'] #read_config(config).get('intervals', [])
    tickers = read_config(config).get('indexes', []).get('nifty50', [])
    indicators = read_config(config).get('indicators', {})  
    tz = read_config(config).get('tz', 'Asia/Kolkata')
    bucket=os.environ.get("INFLUX_BUCKET")
    influx_handler = InfluxDBHandler(tz, url, token, org, bucket, prefix="stock_data")
    # influx_handler.drop_influxdb_bucket()
    # exit(0)
    # influx_handler.create_bucket_if_not_exists()
    
    # for interval in intervals:
    #     data = yf.get_tickers_table(tickers=tickers, interval=interval, tz=tz, indicators=indicators)
    #     for ticker in tickers:
    #         ticker_data = data[ticker] if ticker in data else None
    #         if not ticker_data.empty and not ticker_data is None:
    #             influx_handler.replace_data(ticker=ticker, data=ticker_data, interval=interval)

    print(influx_handler.get_tables())
    df = influx_handler.to_dataframe(interval="2m", ticker="TCS")
    print(df.head(10))
    df = influx_handler.to_dataframe(interval="2m", ticker="BEL")
    print(df.shape)
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

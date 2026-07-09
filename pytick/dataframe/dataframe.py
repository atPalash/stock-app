import logging
import multiprocessing
import os
from dotenv import load_dotenv
import numpy as np
import pandas as pd
import yfinance as yf
import pandas_ta as ta

# from main import mp_process_ticker
from pytick.utility.utility import get_logger, normalize_index_to_tz, read_config, request_server

# Set multiprocessing start method once at module level
try:
    multiprocessing.set_start_method('spawn', force=True)
except RuntimeError:
    pass  # Already set

load_dotenv()
logger = get_logger(__file__, logging.DEBUG)
config = os.environ.get("CONFIG_FILE")
app_config = read_config(file_path=config)


def download_stock_data(ticker: str, interval: str, tz: str, suffix: str="") -> pd.DataFrame:
    """Download stock data from Yahoo Finance.

    Args:
        ticker (str): ticker symbol.
        interval (str): interval for the data. e.g., '1d', '1h'.
        tz (str): timezone, e.g., 'Asia/Kolkata'.
        suffix (str): suffix for the ticker symbol.

    Returns:
        pd.DataFrame: Stock data for the specified ticker and interval.
    """
    ticker_symbol = f"{ticker}{suffix}"
    data = yf.download(
        tickers=[ticker_symbol],
        period="1mo",
        interval=interval,
        progress=False,
        group_by="ticker",
        rounding=True,
        actions=True,
        threads=True,
        multi_level_index=False,
        ignore_tz=True,
        auto_adjust=True,
    )
    data.to_csv(f"{ticker}_{interval}.csv")
    return data


def calculate_indicators(ticker: str, df: pd.DataFrame, indicators: dict) -> dict:
    """Calculate technical indicators for the given DataFrame.

    Args:
        ticker (str): ticker symbol.
        df (pd.DataFrame): dataframe containing stock data.
        indicators (dict): dictionary of indicators to calculate.

    Returns:
        dict: dictionary containing the calculated indicators.
    """
    errors = []
    for ind_type, ind_conf in indicators.items():
        periods = ind_conf.get('periods', [])
        sources = ind_conf.get('sources', [])
        for src in sources:
            src_col = src.lower() if src.lower() in df.columns else src.capitalize()
            for period in periods:
                try:
                    col_name = f"{ind_type}_{period}_{src}"
                    df[col_name] = pd.Series(np.nan, index=df.index)
                    series = None
                    if ind_type == 'sma':
                        series = ta.sma(df[src_col], length=period)
                    elif ind_type == 'ema':
                        series = ta.ema(df[src_col], length=period)
                    elif ind_type == 'atr':
                        series = ta.atr(df['High'], df['Low'],
                                        df['Close'], length=period)
                    elif ind_type == 'vwap':
                        series = ta.vwap(
                            df['High'], df['Low'], df['Close'], df['Volume'])
                    elif ind_type == 'rvol':
                        df["avgVolume"] = df["Volume"].rolling(
                            window=period).mean().shift(1)
                        series = (df["Volume"] / df["avgVolume"])
                        df.drop(columns="avgVolume", inplace=True)
                    elif ind_type == 'rsi':
                        series = ta.rsi(df[src_col], length=period)
                    else:
                        logger.warning(
                            f"Unsupported indicator type: {ind_type}")
                    if series is not None:
                        # only round & assign if we really got a Series
                        df[col_name] = series.round(2)
                except Exception as e:
                    msg = f"Exception calculating {ind_type} for period {period} and source {src}: {e}"
                    errors.append(msg)
    return {'ticker': ticker, 'df': df, 'errors': errors}


def get_nifty_tickers(filename: str) -> list:
    tickers_csv = f"{app_config.get('app_data_path')}/{filename}"
    tickers = pd.read_csv(tickers_csv)
    return tickers['Symbol'].tolist()


class DataFrameHandler:
    def __init__(self, tz: str, indicators: dict, test_data_path: str = None, interval_limits: dict = None):
        self.tables = {}
        self.tz = tz
        self.indicators = indicators
        self.test_data_path = test_data_path
        self.interval_limits = interval_limits 

    def get_tables(self, tickers: list, interval: str) -> dict:
        """Get the OHLC tables for the specified tickers and interval.

        Args:
            tickers (list): list of ticker symbols.
            interval (str): Time interval for the data. e.g., '1d', '1h'.

        Returns:
            dict: A dictionary containing the OHLC data for the specified tickers and interval.
            e.g., {'success': True, 'data': {ticker1: DataFrame, ticker2: DataFrame, ...}}
        """
        ret = {'success': False, 'data': {}}
        try:
            table_interval = self.tables.get(interval, None)
            if table_interval is not None:
                ret['data'] = {k: v for k,
                               v in table_interval.items() if k in tickers}
                ret['success'] = True
        except Exception as e:
            logger.warning(
                f"Exception retrieving DataFrame for interval {interval}: {e}")
        return ret
    
    def set_tables(self, tickers: list, interval: str, suffix: str = '', prefix: str = '') -> dict:
        self.tables[interval] = self.__make_tables(tickers=tickers, interval=interval, suffix=suffix, prefix=prefix)['data']

    def add_tables(self, tickers: list, interval: str, suffix: str = '', prefix: str = '') -> dict:
        new_data = self.__make_tables(tickers=tickers, interval=interval, suffix=suffix, prefix=prefix)['data']
        self.tables[interval].update(new_data)
        
    def __make_tables(self, tickers: list, interval: str, suffix: str = '', prefix: str = '') -> dict:
        """Set the OHLC tables for the specified tickers and interval. sets the
        self.tables[interval] with a dict of {ticker: DataFrame}.

        Args:
            tickers (list): List of ticker symbols.
            interval (str): Time interval for the data. e.g., '1d', '1h'.
        """
        ret = {'success': False, 'data': None}
        try:
            tickers_yf = [
                f"{prefix}{ticker}{suffix}" for ticker in tickers]
            if self.test_data_path is not None:
                # Load test data from CSV files
                ohlc = {}
                for ticker in tickers_yf:
                    cols = pd.read_csv(
                        f"{self.test_data_path}/{ticker}_{interval}.csv", nrows=0).columns
                    date_col = 'Date' if 'Date' in cols else 'Datetime' if 'Datetime' in cols else None
                    df = pd.read_csv(
                        f"{self.test_data_path}/{ticker}_{interval}.csv", parse_dates=[date_col])
                    df.set_index(date_col, inplace=True)
                    ohlc[ticker] = df
            else:
                # Download data from Yahoo Finance
                period = self.interval_limits.get(interval, "1mo")
                ohlc = yf.download(
                    tickers=tickers_yf,
                    period=period,
                    interval=interval,
                    progress=False,
                    group_by="ticker",
                    rounding=True,
                    actions=True,
                    threads=True,
                    multi_level_index=False,
                    ignore_tz=True,
                    auto_adjust=True,
                    timeout=100,
                )
            clean_ohlc = {}
            debug_tickers = ['SBIN.NS', 'TCS.NS', 'ENRIN.NS']  # Add more tickers here if needed
            for ticker in tickers_yf:
                df = ohlc[ticker]  # .xs(ticker, axis=1, level=0)
                if ticker in debug_tickers:
                    logger.debug(f"YF {ticker} interval={interval}: rows={len(df)}, last 5 dates={df.index[-5:].tolist()}")

                df = df.dropna(
                    subset=['Open', 'High', 'Low', 'Close', 'Volume'], how='all')
                if df.empty:
                    logger.warning(f"No data found for ticker: {ticker} interval: {interval}")
                clean_ohlc[ticker] = df
                
            # Prepare the parameters for each process
            num_processes = min(multiprocessing.cpu_count(), len(tickers))
            process_args = [
                (ticker, clean_ohlc[ticker], self.indicators)
                for ticker in tickers_yf
            ]
            result = {}
            try:
                # Use a process pool executor for true parallelism
                with multiprocessing.Pool(processes=num_processes) as pool:
                    # Map the processing function to all tickers with their parameters
                    results = pool.starmap(calculate_indicators, process_args)
            except Exception as e:
                logger.warning(f"Exception during multiprocessing: {e}")
                return ret
            for point in results:
                if suffix and point['ticker'].endswith(suffix):
                    ticker = point['ticker'][:-len(suffix)]
                elif prefix and point['ticker'].startswith(prefix):
                    ticker = point['ticker'][len(prefix):]
                else:
                    ticker = point['ticker']
                df = point['df']
                # Convert columns to lowercase for consistency
                # df = df.replace({np.nan: None})
                df = normalize_index_to_tz(df, self.tz)
                df = df.reset_index()
                df.columns = [c.lower() for c in df.columns]
                if 'date' in df.columns:
                    df = df.rename(columns={'date': 'datetime'})
                result[ticker] = df
                if df is None or df.empty:
                    logger.warning(f"No data found for ticker: {ticker} interval: {interval}")
                if ticker in debug_tickers:
                    logger.debug(f"Indicators {ticker} interval={interval}: rows={len(df)}, last 5 dates={df.datetime[-5:].tolist()}")

            ret['data'] = result
            ret['success'] = True
        except Exception as e:
            logger.warning(
                f"Exception setting DataFrame for interval {interval}: {e}")
        return ret

    def trim_tables(self, interval: str, trim_rows: int):
        """Trim OHLC tables to remove the last N rows for specified tickers.

        Args:
            tickers (list): List of ticker symbols to trim.
            interval (str): Time interval (e.g., '1d', '5m').
            trim_rows (int): Number of rows to remove from the end.

        Returns:
            self: For method chaining.
        """
        if interval not in self.tables:
            logger.warning(f"Interval {interval} not found in tables")
            return self

        if trim_rows < 0:
            logger.warning(f"trim_rows must be positive, got {trim_rows}")
            return self

        if trim_rows > 0:
            self.tables[interval] = {
                ticker: df.iloc[:-trim_rows]
                for ticker, df in self.tables[interval].items()
            }
        return self


if __name__ == "__main__":
    # config_path = "config_debug.yaml"
    # indicators = read_config(config_path).get('indicators', {})
    # set_tables(["BEL", "TCS", "HONASA"], "1d", "Asia/Kolkata", indicators)
    # print(get_nifty_tickers('ind_nifty100list.csv'))
    # import asyncio
    # import json
    # async def main():
    #     # Your async logic goes here
    #     try:
    #         response = await request_server(8000, 'df/SBIN/1mo', {}, timeout=30, method='GET')
    #         print(json.loads(response.text)['data'][-5:])  # Print the last 5 records
    #     except Exception as e:
    #         print(f"An error occurred: {e}")

    # # Use asyncio.run to start the event loop and execute the main function
    # asyncio.run(main())
    download_stock_data("^NSEI", "5m", "Asia/Kolkata")

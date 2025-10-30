import logging
import multiprocessing
import numpy as np
import pandas as pd
import yfinance as yf
import pandas_ta as ta

# from main import mp_process_ticker
from pytick.utility.utility import get_logger, normalize_index_to_tz, read_config

logger = get_logger('yf', logging.DEBUG)

def download_stock_data(ticker:str, interval:str, tz:str)->pd.DataFrame:
    """Download stock data from Yahoo Finance.

    Args:
        ticker (str): ticker symbol.
        interval (str): interval for the data. e.g., '1d', '1h'.
        tz (str): timezone, e.g., 'Asia/Kolkata'.

    Returns:
        pd.DataFrame: Stock data for the specified ticker and interval.
    """
    ticker_symbol = f"{ticker}{'.NS' if tz=='Asia/Kolkata' else ''}"
    data = yf.download(
        tickers=[ticker_symbol],
        period="max",
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
    return data

def calculate_indicators(ticker:str, df: pd.DataFrame, indicators:dict) -> dict:
    """Calculate technical indicators for the given DataFrame.

    Args:
        ticker (str): ticker symbol.
        df (pd.DataFrame): dataframe containing stock data.
        indicators (dict): dictionary of indicators to calculate.

    Returns:
        dict: dictionary containing the calculated indicators.
    """
    for ind_type, ind_conf in indicators.items():
        periods = ind_conf.get('periods', [])
        sources = ind_conf.get('sources', [])
        for src in sources:
            src_col = src.lower() if src.lower() in df.columns else src.capitalize()
            for period in periods:
                try:
                    col_name = f"{ind_type}_{period}_{src}"
                    if ind_type == 'sma':
                        df[col_name] = ta.sma(df[src_col], length=period).round(2)
                    elif ind_type == 'ema':
                        df[col_name] = ta.ema(df[src_col], length=period).round(2)
                    elif ind_type == 'atr':
                        df[col_name] = ta.atr(df['High'], df['Low'], df['Close'], length=period).round(2)
                    elif ind_type == 'vwap':
                        df[col_name] = ta.vwap(df['High'], df['Low'], df['Close'], df['Volume']).round(2)
                    elif ind_type == 'rvol':
                        df["avgVolume"] = df["Volume"].rolling(window=period).mean().shift(1)
                        df[col_name] = (df["Volume"] / df["avgVolume"]).round(2)
                        df.drop(columns="avgVolume", inplace=True)
                    else:
                        logger.warning(f"Unsupported indicator type: {ind_type}")
                except Exception as e:
                    logger.error(f"Error calculating {ind_type} for period {period} and source {src}: {e}")
    return {'ticker': ticker, 'df' : df}

def get_nifty50_tickers() -> list:
    nifty50 = pd.read_csv('ind_nifty50list.csv')
    return nifty50['Symbol'].tolist()
    
class DataFrameHandler:
    def __init__(self, tz:str, indicators:dict):
        self.tables = {}
        self.tz = tz
        self.indicators = indicators
        
    def get_tables(self, tickers:list, interval: str) -> dict:
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
                ret['data'] = {k: v for k, v in table_interval.items() if k in tickers}
                ret['success'] = True
        except Exception as e:
            logger.error(f"Error retrieving DataFrame for interval {interval}: {e}")
        return ret
    
    def set_tables(self, tickers: list, interval: str) -> dict:
        """Set the OHLC tables for the specified tickers and interval. sets the
        self.tables[interval] with a dict of {ticker: DataFrame}.

        Args:
            tickers (list): List of ticker symbols.
            interval (str): Time interval for the data. e.g., '1d', '1h'.
        """
        ret = {'success': False, 'data': None}
        try:
            tickers_yf = [f"{ticker}{'.NS' if self.tz=='Asia/Kolkata' else ''}" for ticker in tickers]
            ohlc = yf.download(
                tickers=tickers_yf,
                period="max",
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
            clean_ohlc = {}
            for ticker in tickers_yf:
                df = ohlc[ticker] #.xs(ticker, axis=1, level=0)
                df = df.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'], how='all')
                if df.empty:
                    logger.warning(f"No data found for ticker: {ticker}")
                clean_ohlc[ticker] = df

            # Create a pool of processes (one for each CPU core)
            num_processes = min(multiprocessing.cpu_count(), len(tickers))
            # Prepare the parameters for each process
            process_args = [
                (ticker, clean_ohlc[ticker], self.indicators)
                for ticker in tickers_yf
            ]
            result = {}
            # Use a process pool executor for true parallelism
            with multiprocessing.Pool(processes=num_processes) as pool:
                # Map the processing function to all tickers with their parameters
                results = pool.starmap(calculate_indicators, process_args)

            for point in results:
                ticker = point['ticker'].split('.')[0]
                df = point['df']
                # Convert columns to lowercase for consistency
                # df = df.replace({np.nan: None})
                df = normalize_index_to_tz(df, self.tz)
                df = df.reset_index()
                df.columns = [c.lower() for c in df.columns]
                result[ticker] = df
                if df is None or df.empty:
                    logger.warning(f"No data found for ticker: {ticker}")

            self.tables[interval] = result
            ret['success'] = True
        except Exception as e:
            logger.error(f"Error setting DataFrame for interval {interval}: {e}")
        return ret
        

if __name__ == "__main__":
    # config_path = "config_debug.yaml"
    # indicators = read_config(config_path).get('indicators', {})
    # get_tickers_table(["BEL", "TCS", "HONASA"], "1d", "Asia/Kolkata", indicators)
    print(get_nifty50_tickers())

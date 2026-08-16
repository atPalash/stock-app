import logging
import os

from dotenv import load_dotenv
import pandas as pd
import yfinance as yf

from pytick.utility.utility import get_logger, read_config


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

def get_nse_option_symbols():
    all_options_tickers = pd.read_csv(f"{app_config.get('app_data_path')}/instruments.csv")
    all_options_tickers = all_options_tickers[all_options_tickers["exchange"] == "NFO"]
    all_options_symbols = all_options_tickers["name"].unique().tolist()
    print(all_options_symbols)

if __name__ == "__main__":
    get_nse_option_symbols()
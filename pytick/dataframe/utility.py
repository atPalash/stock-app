import logging
import os

from dotenv import load_dotenv
import pandas as pd
import yfinance as yf

from pytick.utility.utility import get_app_config, get_logger, read_config


load_dotenv()
logger = get_logger(__file__, logging.DEBUG)
app_config, _ = get_app_config()

def download_stock_data(tickers: list, interval: str, period: str, suffix: str="") -> pd.DataFrame:
    """Download stock data from Yahoo Finance.

    Args:
        tickers (list): list of ticker symbols.
        interval (str): interval for the data. e.g., '1d', '1h'.
        period (str): period for the data. e.g., '1mo', '3mo'.
        suffix (str): suffix for the ticker symbol.

    Returns:
        pd.DataFrame: Stock data for the specified ticker and interval.
    """
    tickers_yf = [f"{ticker}{suffix}" for ticker in tickers]
    data = yf.download(
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
    # data.to_csv(f"{ticker}_{interval}.csv")
    return data

def get_nse_option_symbols():
    all_options_tickers = pd.read_csv(f"{app_config.get('app_data_path')}/instruments.csv")
    all_options_tickers = all_options_tickers[all_options_tickers["exchange"] == "NFO"]
    all_options_symbols = all_options_tickers["name"].unique().tolist()
    print(all_options_symbols)

if __name__ == "__main__":
    # get_nse_option_symbols()
    download_stock_data(["AAPL", "MSFT"], "5m", "1mo")
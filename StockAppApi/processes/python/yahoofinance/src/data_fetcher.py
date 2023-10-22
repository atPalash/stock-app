import multiprocessing
import yfinance as yf
import pandas
import time
from inspect import currentframe, getframeinfo
from yahoofinancials import YahooFinancials

from StockAppApi.base.python.src import json_helper


def __download_df_from_yahoo(tickers, period, interval):
    try:
        data = yf.download(
            tickers=tickers,
            period=period,
            interval=interval,
            progress=False,
            group_by="ticker",
            rounding=True,
            actions=True,
            threads=10,
            show_errors=True,
        )
        data = data.dropna()
        return data
    except Exception as e:
        raise


def __get_csv_from_yahoo(ticker, period, interval, destination):
    try:
        data = __download_df_from_yahoo(
            tickers=ticker, period=period, interval=interval
        )
        csv_name = "{}/{}".format(destination, ticker.split(".")[0])
        data.to_csv(csv_name + ".csv")
    except Exception as e:
        raise


def download_latest_data(tickers: list):
    try:
        data = yf.download(
            tickers=tickers,
            period="1d",
            interval="1m",
            progress=False,
            group_by="ticker",
            rounding=True,
            actions=True,
            threads=10,
            show_errors=True,
        )
        data = data.dropna().tail(1)
        return data
    except Exception as e:
        raise


def download_historical_data(
    tickers: list,
    period: int,
    interval: int,
    as_panda_df=False,
    as_csv=False,
    destination="",
):
    """Download ohlc data from yahoo finance. When the desired return value is
    pandas dataframe the number of rows are realligned to match dataframe for all
    the stocks, this causes dropping of older rows for some tickers, since the new
    tickers donot contain older data.

    Hence, for downloading to csv each ticker is downloaded as a separate ticker
    using multiple threads in parallel.

    Args:
        tickers (list): list of tickers
        period (int): maximum duration of data points. e.g. 5y, 10y, max
        interval (int): each row interval. e.g. 1d, 1h
        as_panda_df (bool, optional): return as pandas dataframe grouped by ticker.
        Defaults to False.
        as_csv (bool, optional): download the tickers to csv. Defaults to False.
        destination (str, optional): path to where to download. Defaults to "".

    Returns:
        _type_: _description_
    """
    errors = ""
    ret = None
    try:
        if as_csv:
            args = []
            for ticker in tickers:
                args.append((ticker, period, interval, destination))
            # Create a pool of worker processes
            with multiprocessing.Pool() as pool:
                pool.starmap(__get_csv_from_yahoo, args)

        if as_panda_df:
            ret = __download_df_from_yahoo(
                tickers=tickers, period=period, interval=interval
            )
    except Exception as e:
        frameinfo = getframeinfo(currentframe())
        errors += f"{frameinfo.filename, frameinfo.lineno}:{e.args}"
    return ret, errors


def __download_fundamentals_from_yahoo(tickers: list, destination: str):
    error = ""
    try:
        args = []
        for ticker in tickers:
            args.append((ticker,))
            # Create a pool of worker processes
        with multiprocessing.Pool() as pool:
            financial_statements = pool.starmap(__fetch_fundamentals, args)

        for row in financial_statements:
            for key, value in row.items():
                if "error" in value:
                    error += f"{key}: {value}"
                json_helper.save_json(input=value, filepath=f"{destination}/{key}.json")
        return error
    except Exception as e:
        raise


def __fetch_fundamentals(ticker: str):
    print("__fetch_fundamentals ", ticker)
    ticker_name = ticker.split(".")[0]
    try:
        financial_statements = {}

        def insert_to_ret(value: dict):
            key = list(value.keys())[0]
            if ticker_name not in financial_statements:
                financial_statements[ticker_name] = {}
            financial_statements[ticker_name][key] = value[key][ticker]

        yahoo_financials = YahooFinancials(ticker, timeout=10)
        # For some reason for-loop doesn't seem to fetcht the data properly.
        # using explicit call of the methods
        insert_to_ret(yahoo_financials.get_financial_stmts("quarterly", "income"))
        insert_to_ret(yahoo_financials.get_financial_stmts("quarterly", "balance"))
        insert_to_ret(yahoo_financials.get_financial_stmts("quarterly", "cash"))
        insert_to_ret(yahoo_financials.get_financial_stmts("annual", "income"))
        insert_to_ret(yahoo_financials.get_financial_stmts("annual", "balance"))
        insert_to_ret(yahoo_financials.get_financial_stmts("annual", "cash"))

        return financial_statements
    except Exception as e:
        return {ticker_name: f"{ticker} fundamental download error"}


def download_stock_stats(tickers: list, destination):
    try:
        error = __download_fundamentals_from_yahoo(
            tickers=tickers, destination=destination
        )
        return error
    except Exception as e:
        frameinfo = getframeinfo(currentframe())
        error = f"{frameinfo.filename, frameinfo.lineno}:{e.args}"
        return error


if __name__ == "__main__":
    try:
        download_historical_data(
            tickers=["BEL.NS", "ABB.NS"],
            period="1mo",
            interval="15m",
            as_csv=True,
            destination="/home/palash/dev/stock-app/test",
        )
    except Exception as e:
        print(e.args)
"""
        frequencies = ['quaterly', 'annual']
        statements = ['income', 'balance', 'cash']
        
        for frequency in frequencies:
            for statement in statements:
                insert_to_ret(yahoo_financials.get_financial_stmts(frequency, statement))
"""

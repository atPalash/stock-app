from stock_app_py.system.src.steps.given import ignore, stocks

import re


def extract_stock_list(stock_list: str):
    ticker_str = stock_list.replace(" ", "")
    return {
        "tickers": ticker_str.split(",") if "," in ticker_str else [ticker_str],
        "exception": None,
    }


def get_steps():
    return {
        # r'^(\w+)\s+(\d+)\s+stocks$': get_stocks_in_index,
        r"^(\w+)\s+stocks$": stocks.get_index_stocks,
        r"^stocks (\w+(?:,*\s*\w*)*)$": stocks.get_stocks,
        r"^ignore\s+stocks\s+(\w+(?:,*\s*\w*)*)$": ignore.ignore_stocks
        # r'^indexes (\w+(?:,*\s*\w*)*)$': get_stocks
    }

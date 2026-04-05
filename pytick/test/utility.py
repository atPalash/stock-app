
import os

from curl_cffi.requests import query
from dotenv import load_dotenv
import logging

import pandas as pd

from pytick.dataframe.dataframe import DataFrameHandler
from pytick.dataframe.dataframe import DataFrameHandler
from pytick.query.query import QueryHandler
from pytick.utility.utility import read_config, get_logger

logger = get_logger(__file__, logging.DEBUG)
load_dotenv()
app_config = read_config(file_path=os.environ.get("CONFIG_FILE"))


class DummyNotificationHandler:
    def __init__(self, tz=None):
        self.tz = tz

    def get_corporate_actions(self, *args, **kwargs):
        return {}

    def get_corporate_actions_dfs(self, *args, **kwargs):
        df = pd.read_csv(
            f"{app_config.get('pytick_test_path', '')}/data/corporate_actions.csv", parse_dates=['datetime'])
        df["datetime"] = pd.to_datetime(df['datetime'], format='%d-%b-%Y %H:%M:%S').\
            dt.tz_localize(self.tz)
        tickers = kwargs.get('tickers', [])
        ret = {}
        for ticker in tickers:
            ticker_df = df[df["symbol"] == ticker]
            ret[ticker] = ticker_df if not ticker_df.empty else None
        return ret


class TestQueryHandler:
    def __init__(self):
        self.tickers = ["TCS", "BEL", "SBIN", "TMPV"]
        self.indicators = app_config.get('indicators', {})
        self.cron_schedules = app_config.get('cron_schedules', {})
        self.cron_notification = app_config.get('cron_notification', {})
        self.tz = app_config.get('tz', 'Asia/Kolkata')
        self.data_handler = DataFrameHandler(
            tz=self.tz, indicators=self.indicators, test_data_path=f"{app_config.get('pytick_test_path', '')}/data")
        self.data_handler.set_tables(self.tickers, "1d")
        self.data_handler.set_tables(self.tickers, "5m")
        self.notification_handler = DummyNotificationHandler(tz=self.tz)
        self.gherkin_handler = QueryHandler(data_handler=self.data_handler,
                                            notification_handler=self.notification_handler,
                                            interval_translation={v: k for k, v in app_config.get(
                                                'interval_translation', {}).items()},
                                            interval_seconds=app_config.get('interval_seconds', {}))

    def getQueryHandler(self):
        return self.gherkin_handler


if __name__ == "__main__":
    gherkin = """
Feature: pytick llm  
Scenario: Test index not found error 
Given stocks from index nifty50  
When let ema10 = latest in 20 samples of minute5 close ema 10  
* let close = latest in 20 samples of minute5 close
* let notification = latest in 20 samples of minute5 notification
Then list bull = tickers with (close > ema10) & notification
* list bear = tickers with (close < ema10) & notification
"""
    handler = TestQueryHandler().getQueryHandler()
    result = handler.get_gherkin_result(gherkin_str=gherkin)
    print("Result:", result)
    print("Testing invalid index scenario...")

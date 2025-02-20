import os
import re
import subprocess
import time
import pandas
import csv

# from stock_app_py.system.src.command_handler import CommandHandler
from stock_app_py.system.src.gherkin_query_ohlc_helper import GherkinQueryOhlcHelper
from stock_app_py.system.src.yahoo_finance import YahooFinance

from stock_app_py.utility.src.csv_checker import is_csv_html
from stock_app_py.utility.src.logger import get_logger
from stock_app_py.utility.src.path_helper import get_app_path
from stock_app_py.utility.src.yaml_parser import read_config, save_config
from stock_app_py.system.base.system import System
from stock_app_py.system.interface.system_if import RetVal

logger = get_logger(__name__)


class GherkinBacktestOhlcHelper(GherkinQueryOhlcHelper):
    def __init__(
        self,
        indicator_config_file: str,
        selected_stocks_config_file: str,
        parameter: dict,
        command_handler: object,
        name="",
    ) -> None:
        """Read the ohlc data required during gherkin query. This class is a helper
        for gherkin query which keeps track of the tickers and its corresponding
        ohlc data. Primarily it stores a map to be fetched by gherkin query.
        map {
            <interval1> :
            {
                <ticker>: <ohlc>
            },
            <interval2> :
            {
                <ticker>: <ohlc>
            }
        }
        Args:
            indicator_config_file (str): indicator configuration
            selected_stocks_config_file (str): selected stocks list
            parameter (dict): key-value pairs for setting up the query
            command_handler (object): to call other systems
            name (str, optional): Name of the query. Defaults to "".
        """
        super().__init__(
            indicator_config_file=indicator_config_file,
            selected_stocks_config_file=selected_stocks_config_file,
            parameter=parameter,
            command_handler=command_handler,
            name=name,
        )
        self.commands = {"get": self.__get}
        self.yf = YahooFinance(
            indicator_config_file=indicator_config_file,
            selected_stocks_config_file=selected_stocks_config_file,
            parameter={},
            command_handler=None,
            name="",
        )
        self.gherkin_ohlc = {}
        for interval, duration in self.yf.get_intervals_duration().items():
            self.gherkin_ohlc[interval] = {"duration": duration}
        self.parameter["lookback"] = parameter["lookback"]

    def __get(self, interval: str, ticker: str) -> pandas.DataFrame:
        """Return dict with selected stocks.
        Returns:
            RetVal: selected stock config
        """
        try:
            return self.gherkin_ohlc[interval][ticker]
        except Exception as e:
            raise

    def __fetch_ohlc(self, interval: str, tickers: list):
        """Read ohlc data for the tickers and specified interval as arg, sync it with
        the base interval send in parameter

        Args:
            interval (str): interval of data to update

        Returns:
            RetVal: return None
        """
        sync_interval = self.parameter["interval"]
        for ticker in tickers:
            try:
                ret = self.yf.read_ohlc(interval=interval, ticker=ticker).obj
                self.gherkin_ohlc[interval][ticker] = self.__sync_with_base(
                    sync_interval=sync_interval, query_interval=interval, ohlc=ret
                )

            except Exception as e:
                logger.error("ERROR yahoo gherking ohlc make", e.args, ticker)

    def __sync_with_base(
        self, sync_interval: str, query_interval: str, ohlc: pandas.DataFrame
    ) -> pandas.DataFrame:
        """Sync current interval to base interval

        Args:
            sync_interval (str): _description_
            query_interval (str): _description_
            ohlc (pandas.DataFrame): _description_

        Returns:
            pandas.DataFrame: _description_
        """
        look_back_in_query = self.__conversion(
            sync_interval=sync_interval, query_interval=query_interval
        )
        ret = ohlc.iloc[:-look_back_in_query]
        return ret

    def __conversion(self, sync_interval, query_interval):
        trading_minutes_in_day = 375
        conversion_factors = {
            "week": 5 * trading_minutes_in_day,
            "day": trading_minutes_in_day,
            "hour": 60,
            "minute30": 30,
            "minute15": 15,
            "minute5": 5,
        }
        sync_minutes = conversion_factors[sync_interval]
        query_minutes = conversion_factors[query_interval]

        look_back_in_sync = self.parameter["lookback"]
        look_back_in_minutes = look_back_in_sync * sync_minutes
        look_back_in_query = int(look_back_in_minutes / query_minutes) + 1
        return look_back_in_query

    def get_interval_map(self, interval: str, tickers: list):
        try:
            self.__fetch_ohlc(interval=interval, tickers=tickers)
            return self.gherkin_ohlc[interval]
        except Exception as e:
            logger.error("ERROR yahoo gherking ohlc make", e.args)

    def get_ohlc_on_both_window_end(self, tickers, window):
        sync_interval = self.parameter["interval"]
        ret = {}
        for ticker in tickers:
            try:
                ohlc = self.yf.read_ohlc(interval=sync_interval, ticker=ticker).obj
                look_back_in_query = self.__conversion(
                    sync_interval=sync_interval, query_interval=sync_interval
                )
                start = ohlc.iloc[-look_back_in_query]
                end = ohlc.iloc[-look_back_in_query + window]
                ret[ticker] = {
                    "start": start,
                    "end": end,
                    "bull": end["Close"] > start["Close"],
                    "bear": end["Close"] < start["Close"],
                }
            except Exception as e:
                logger.error("ERROR yahoo gherking ohlc make", ret.errors, ticker)
        return ret


if __name__ == "__main__":
    indicator_config_yaml = get_app_path("indicator.yaml")
    selected_stocks_yaml = get_app_path("selected_stocks.yaml")
    ut = GherkinBacktestOhlcHelper(
        indicator_config_file=indicator_config_yaml,
        selected_stocks_config_file=selected_stocks_yaml,
        command_handler=None,
        parameter={"lookback": 100, "interval": "day"},
        name="",
    )
    ut.get_interval_map("week", tickers=["BEL", "TCS"])

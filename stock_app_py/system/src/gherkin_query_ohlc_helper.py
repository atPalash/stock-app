import os
import re
import subprocess
import time
import pandas
import csv
# from stock_app_py.system.src.command_handler import CommandHandler
from stock_app_py.system.src.yahoo_finance import YahooFinance

from stock_app_py.utility.src.csv_checker import is_csv_html
from stock_app_py.utility.src.path_helper import get_app_path
from stock_app_py.utility.src.yaml_parser import read_config, save_config
from stock_app_py.system.base.system import System
from stock_app_py.system.interface.system_if import RetVal


class GherkinQueryOhlcHelper(System):
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
                timestamp: <creation time>
                <ticker>: <ohlc>
            },
            <interval2> :
            {
                timestamp: <creation time>
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
        # self.command_handler = CommandHandler(
        #     indicator_config_yaml=indicator_config_file,
        #     selected_stocks_yaml=selected_stocks_config_file,
        # )
        self.commands = {
            "get": self.__get,
            "update": self.__update,
        }
        self.yf = YahooFinance(
            indicator_config_file=indicator_config_file,
            selected_stocks_config_file=selected_stocks_config_file,
            parameter={},
            command_handler=None,
            name="",
        )
        self.gherkin_ohlc = {}
        for interval,duration in self.yf.get_intervals_duration().items():
            self.gherkin_ohlc[interval] = { 'duration': duration }

    def __get(self, interval: str, ticker: str) -> pandas.DataFrame:
        """Return dict with selected stocks.
        Returns:
            RetVal: selected stock config
        """
        try:
            return self.gherkin_ohlc[interval][ticker]
        except Exception as e:
            raise

    def __update(self, intervals: list, tickers: list):
        """Read ohlc data for the tickers and specified intervals

        Args:
            interval (str): interval of data to update

        Returns:
            RetVal: return None
        """
        timestamp_minutes = time.time() / 60  # timestamp is in minute
        for interval in intervals:
            self.gherkin_ohlc[interval]["timestamp"] = timestamp_minutes
            for ticker in tickers:
                ret = self.yf.read_ohlc(interval=interval, ticker=ticker)
                self.gherkin_ohlc[interval][ticker] = ret.obj
                if ret.errors != "":
                    print("ERROR yahoo gherking ohlc make", ret.errors)

    def get_intervals(self) -> list:
        return self.gherkin_ohlc.keys()

    def get_interval_map(self, interval:str, tickers:list):
        # first check if update is required, i.e the timestamp is older than interval
        if 'timestamp' not in self.gherkin_ohlc[interval]:
            self.__update(intervals=[interval], tickers=tickers)
        else:
            timestamp_minutes = time.time() / 60
            last_update_time = self.gherkin_ohlc[interval]['timestamp']
            if (timestamp_minutes - last_update_time) > self.gherkin_ohlc[interval]['duration']:
                self.__update(intervals=[interval], tickers=tickers)
        return self.gherkin_ohlc[interval]


if __name__ == "__main__":
    indicator_config_yaml = get_app_path("indicator.yaml")
    selected_stocks_yaml = get_app_path("selected_stocks.yaml")
    yf = GherkinQueryOhlcHelper(
        indicator_config_file=indicator_config_yaml,
        selected_stocks_config_file=selected_stocks_yaml,
        parameter={},
        command_handler=None,
        name="",
    )
    # https://www.niftyindices.com/IndexConstituent/ind_niftyautolist.csv
    # https://www.niftyindices.com/IndexConstituent/nifty_low_Volatility50_Index.csv
    # https://www.niftyindices.com/IndexConstituent/ind_niftyoilgaslist.csv
    # javascript:;
    yf.update(intervals=["day"], tickers=["ABB", "TCS"])
    data = yf.get(interval="day", ticker="ABB")
    print(data)

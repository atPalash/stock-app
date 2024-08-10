import pandas
import numpy
from scipy.stats import linregress

from stock_app_py.talib.interface.indicator_if import IndicatorIf
from stock_app_py.yahoofinance.src.data_fetcher import download_latest_data


class Indicator(IndicatorIf):
    def __init__(
        self, ohlc: pandas.DataFrame, parameter: dict, ticker: str, name="", type=""
    ) -> None:
        self.name = name
        self.type = type  # indicatpr can also have sub-types
        self.ticker = ticker
        self.ohlc = ohlc
        self.parameter = parameter

    def _do_analysis(self, latest=1):
        pass

    def get_result_df(self, with_latest_minute=1) -> pandas.DataFrame:
        """Get the result as pandas dataframe

        Returns:
            dict: pandas dataframe with additional column for analysed data
        """
        self._do_analysis(latest=with_latest_minute)
        return self.ohlc

    def parse_indicator_setting(self, setting: str, keys: list):
        if setting != "":
            settings = setting.replace(" ", "").split(",")
            i = 0
            for setting in settings:
                self.parameter[keys[i]] = setting
                i += 1

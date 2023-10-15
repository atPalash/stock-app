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

    def get_data(self, latest=True):
        if latest == 1:
            tickers = []
            if "^" in self.ticker:  # index are with ^in yahoo
                tickers = [self.ticker]
            else:
                tickers = [f"{self.ticker}.NS"]
            last_minute_series = download_latest_data(tickers=tickers)
            self.ohlc = pandas.concat([self.ohlc, last_minute_series])
        return self.ohlc

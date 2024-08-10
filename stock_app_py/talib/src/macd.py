import talib
import numpy
import pandas
from scipy.stats import linregress

from stock_app_py.talib.base.indicator import Indicator
from stock_app_py.yahoofinance.src.data_fetcher import download_latest_data


class Macd(Indicator):
    """MACD indicator it supports 3 sub-indicators
    1. MACD
    2. MACD signal
    3. MACD histogram

    Args:
        Indicator (_type_): _description_
    """

    def __init__(self, ohlc, parameter, ticker: str, name="", type="") -> None:
        super().__init__(
            name=name, type=type, ticker=ticker, ohlc=ohlc, parameter=parameter
        )

    def _do_analysis(self, latest=True):
        self.parse_indicator_setting(
            self.parameter["indicator_setting"],
            ["window", "macd_fast_period", "macd_slow_period", "macd_signal_period"],
        )
        macd, macdsignal, macdhist = talib.MACD(
            self.ohlc[self.parameter["ohlc"]],
            fastperiod=self.parameter["macd_fast_period"],
            slowperiod=self.parameter["macd_slow_period"],
            signalperiod=self.parameter["macd_signal_period"],
        )
        macd = numpy.around(macd, decimals=2)
        macdsignal = numpy.around(macdsignal, decimals=2)
        macdhist = numpy.around(macdhist, decimals=2)
        self.ohlc.loc[:, "macd"] = macd
        self.ohlc.loc[:, "macdsignal"] = macdsignal
        self.ohlc.loc[:, "macdhist"] = macdhist

        return macd, macdsignal, macdhist

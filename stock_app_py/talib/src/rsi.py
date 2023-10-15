import talib
import numpy
import pandas
from scipy.stats import linregress

from stock_app_py.talib.base.indicator import Indicator
from stock_app_py.yahoofinance.src.data_fetcher import download_latest_data


class Rsi(Indicator):
    def __init__(self, ohlc, parameter, ticker: str, name="", type="") -> None:
        super().__init__(
            name=name, type=type, ticker=ticker, ohlc=ohlc, parameter=parameter
        )

    def _do_analysis(self, latest=True):
        self.ohlc = self.get_data(latest=latest)
        rsi = talib.RSI(
            self.ohlc[self.parameter["ohlc"]], timeperiod=int(self.parameter["window"])
        )
        rsi = numpy.around(rsi, decimals=2)
        self.ohlc.loc[:, "rsi"] = rsi
        return rsi

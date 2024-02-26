import talib
import numpy
import pandas

from stock_app_py.talib.base.indicator import Indicator


class Volatility(Indicator):
    def __init__(self, ohlc, parameter, ticker: str, name="", type="") -> None:
        super().__init__(
            name=name, type=type, ticker=ticker, ohlc=ohlc, parameter=parameter
        )

    def _do_analysis(self, latest=1):
        atr = talib.ATR(
            self.ohlc['High'], self.ohlc['Low'], self.ohlc['Close'], timeperiod=int(self.parameter["window"])
        )
        atr = numpy.around(atr, decimals=2)
        self.ohlc.loc[:, "atr"] = atr
        return atr

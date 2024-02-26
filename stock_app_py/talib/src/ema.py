import talib
import numpy
import pandas

from stock_app_py.talib.base.indicator import Indicator


class Ema(Indicator):
    def __init__(self, ohlc, parameter, ticker: str, name="", type="") -> None:
        super().__init__(
            name=name, type=type, ticker=ticker, ohlc=ohlc, parameter=parameter
        )

    def _do_analysis(self, latest=1):
        ema = talib.EMA(
            self.ohlc[self.parameter["ohlc"]], timeperiod=int(self.parameter["window"])
        )
        ema = numpy.around(ema, decimals=2)
        self.ohlc.loc[:, "ema"] = ema
        return ema

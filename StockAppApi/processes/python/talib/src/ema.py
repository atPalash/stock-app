import talib
import numpy
import pandas

from StockAppApi.processes.python.talib.base.indicator import Indicator
from StockAppApi.processes.python.yahoofinance.src.data_fetcher import download_latest_data

class Ema(Indicator):
    def __init__(self, ohlc, parameter, ticker:str, name="", type="") -> None:
        super().__init__(name=name, type=type, ticker=ticker, ohlc=ohlc, parameter=parameter)

    def _do_analysis(self, latest=1):
        self.ohlc = self.get_data(latest=latest)
        ema = talib.EMA(self.ohlc[self.parameter['ohlc']], timeperiod=int(self.parameter['window']))
        ema = numpy.around(ema, decimals=2)
        self.ohlc.loc[:, 'ema'] = ema
        return ema
    
import talib
import numpy
import pandas

from StockAppApi.processes.python.talib.base.indicator import Indicator
from StockAppApi.processes.python.yahoofinance.src.data_fetcher import download_latest_data

class Ma(Indicator):
    def __init__(self, ohlc, parameter, ticker:str, name="", type="") -> None:
        super().__init__(name=name, type=type, ticker=ticker, ohlc=ohlc, parameter=parameter)

    def _do_analysis(self, latest=1):
        self.ohlc = self.get_data(latest=latest)
        ma = talib.MA(self.ohlc[self.parameter['ohlc']], timeperiod=int(self.parameter['window']))
        ma = numpy.around(ma, decimals=2)
        self.ohlc.loc[:, 'ma'] = ma
        return ma
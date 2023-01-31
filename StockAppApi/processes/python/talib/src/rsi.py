import talib
import numpy
import pandas
from scipy.stats import linregress

from StockAppApi.processes.python.talib.base.indicator import Indicator
from StockAppApi.processes.python.yahoofinance.src.data_fetcher import download_latest_data

class Rsi(Indicator):
    def __init__(self, ohlc, parameter, ticker:str, name="", type="") -> None:
        super().__init__(name=name, type=type, ticker=ticker, ohlc=ohlc, parameter=parameter)
        
    def _do_analysis(self, latest=True):
        if latest == 1:
            last_minute_series = download_latest_data(tickers=[f'{self.ticker}.NS'])
            self.ohlc = pandas.concat([self.ohlc, last_minute_series], ignore_index=True)
        rsi = talib.RSI(self.ohlc[self.parameter['ohlc']], timeperiod=int(self.parameter['window']))
        rsi = numpy.around(rsi, decimals=2)
        self.ohlc.loc[:,'rsi'] = rsi
        return rsi
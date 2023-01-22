import talib
import numpy
import pandas
from scipy.stats import linregress

from StockAppApi.processes.python.talib.base.indicator import Indicator
from StockAppApi.processes.python.yahoofinance.src.data_fetcher import download_latest_data

class Macd(Indicator):
    """MACD indicator it supports 3 sub-indicators
    1. MACD
    2. MACD signal
    3. MACD histogram

    Args:
        Indicator (_type_): _description_
    """
    def __init__(self, ohlc, parameter, ticker:str, name="", type="") -> None:
        super().__init__(name=name, type=type, ticker=ticker, ohlc=ohlc, parameter=parameter)
        
    def _do_analysis(self, latest=True):
        if latest == 1:
            last_minute_series = download_latest_data(tickers=[f'{self.ticker}.NS'])
            self.ohlc = pandas.concat([self.ohlc, last_minute_series])
        macd, macdsignal, macdhist = talib.MACD(self.ohlc[self.parameter['ohlc']], 
                                                fastperiod=self.parameter['macd_fast_period'],
                                                slowperiod=self.parameter['macd_slow_period'],
                                                signalperiod=self.parameter['macd_signal_period'])
        macd = numpy.around(macd, decimals=2)
        macdsignal = numpy.around(macdsignal, decimals=2)
        macdhist = numpy.around(macdhist, decimals=2)
        self.ohlc['macd'] = macd
        self.ohlc['macdsignal'] = macdsignal
        self.ohlc['macdhist'] = macdhist
        
        return macd, macdsignal, macdhist
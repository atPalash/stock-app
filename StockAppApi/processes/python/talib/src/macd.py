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
    def __init__(self, name, type ,ticker, ohlc, parameter) -> None:
        super().__init__(name=name, type=type, ticker=ticker, ohlc=ohlc, parameter=parameter)
        
        # add additional command on top of base indicator supported commands
        self.supported_command.update({
            'where': self.__where
        })
        
    def __where(self, condition:str) -> dict:
        """Search for instances where the condition is satisfied

        Args:
            condition (str): condition which checks with the macd or macd signal
            or macd histogram 

        Returns:
            dict: analysis status with pandas dataframe
        """
        self._do_analysis()
        try:
            if 'value' in condition:
                condition = condition.replace("value", f'self.ohlc["{self.type}"]')
                return self._result(status=True, obj=self.ohlc.loc[eval(condition)])
            elif 'diff' in condition:
                condition = condition.replace("diff", f'self.ohlc["{self.type}"].diff()')
                return self._result(status=True, obj=self.ohlc.loc[eval(condition)])
        except Exception as e:
            raise
        return self._result(status=False, obj=None)

    def _do_analysis(self):
        last_minute_series = download_latest_data(tickers=[f'{self.ticker}.NS'])
        self.ohlc = pandas.concat([self.ohlc, last_minute_series])
        macd, macdsignal, macdhist = talib.MACD(self.ohlc[self.parameter['ohlc']], 
                                                fastperiod=self.parameter['fastperiod'],
                                                slowperiod=self.parameter['slowperiod'],
                                                signalperiod=self.parameter['signalperiod'])
        macd = numpy.around(macd, decimals=2)
        macdsignal = numpy.around(macdsignal, decimals=2)
        macdhist = numpy.around(macdhist, decimals=2)
        self.ohlc['macd'] = macd
        self.ohlc['macdsignal'] = macdsignal
        self.ohlc['macdhist'] = macdhist
        
        return macd
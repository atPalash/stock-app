import talib
import numpy
import pandas

from StockAppApi.processes.python.talib.base.indicator import Indicator
from StockAppApi.processes.python.yahoofinance.src.data_fetcher import download_latest_data

class Ema(Indicator):
    def __init__(self, name, type, ticker, ohlc, parameter) -> None:
        super().__init__(name=name, type=type, ticker=ticker, ohlc=ohlc, parameter=parameter)
        
        # add additional command on top of base indicator supported commands
        self.supported_command.update({
            'where': self.__where
        })
        
    def __where(self, condition:str) -> dict:
        """Search for instances where the condition is satisfied

        Args:
            condition (str): condition which checks with the ema value

        Returns:
            dict: analysis status with pandas dataframe
        """
        self._do_analysis()
        try:
            if 'value' in condition:
                condition = condition.replace("value", "self.ohlc['ema']")
                return self._result(status=True, obj=self.ohlc.loc[eval(condition)])
        except Exception as e:
            raise
        return self._result(status=False, obj=None)

    def _do_analysis(self):
        last_minute_series = download_latest_data(tickers=[f'{self.ticker}.NS'])
        self.ohlc = pandas.concat([self.ohlc, last_minute_series])
        ema = talib.EMA(self.ohlc[self.parameter['ohlc']], timeperiod=int(self.parameter['window']))
        ema = numpy.around(ema, decimals=2)
        self.ohlc['ema'] = ema
        return ema
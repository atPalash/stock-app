import pandas
import numpy
from scipy.stats import linregress

from StockAppApi.processes.python.talib.interface.indicator_if import IndicatorIf

class Indicator(IndicatorIf):
    def __init__(self, name: str, type:str, ticker: str,ohlc:pandas.DataFrame, parameter:dict) -> None:
        self.name = name
        self.type = type # indicatpr can also have sub-types
        self.ticker = ticker
        self.ohlc = ohlc
        self.parameter = parameter
        self.supported_command = {
            'latest': self._latest,
            'slope': self._slope
        }
    
    def execute_command(self, command:str, condition="")->dict:
        try:
            return self.supported_command[command](condition)
        except Exception as e:
            raise
    
    def _latest(self, condition:str):
        """Get the latest n rows with indicator result

        Args:
            condition (str): an empty string 

        Returns:
            _type_: status and latest macd
        """
        self._do_analysis()
        n = int(condition.split("=")[1])
        return self._result(status=True, obj=self.ohlc.tail(n))

    def _slope(self, condition:str) -> dict:
        """find slope of indicator type

        Args:
            condition (str): last N instances

        Returns:
            dict: of status with slope data
        """
        self._do_analysis()
        
        if condition == "":
            data = self.ohlc[self.type]    
        else:
            n = int(condition.split("=")[1])
            data = self.ohlc.tail(n)[self.type]
        data = data.dropna()
        slope, intercept, _, _, _ = linregress(numpy.arange(0, data.shape[0], 1), data)
        return self._result(status=True, obj={
            'slope': slope,
            'intercept': intercept
        })
    
    def _do_analysis(self):
        pass
    
    def _result(self, status: bool, obj: object) -> dict:
        return {'name':self.name, 'status': status, 'result': obj}
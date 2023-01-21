import pandas
import numpy
from scipy.stats import linregress

from StockAppApi.processes.python.talib.interface.indicator_if import IndicatorIf

class Indicator(IndicatorIf):
    def __init__(self, ohlc:pandas.DataFrame, parameter:dict,ticker:str, name="", type="") -> None:
        self.name = name
        self.type = type # indicatpr can also have sub-types
        self.ticker = ticker
        self.ohlc = ohlc
        self.parameter = parameter
 
    def _do_analysis(self, latest=True):
        pass
    
    def get_result_df(self, with_latest_minute=True) -> pandas.DataFrame:
        """Get the result as pandas dataframe 

        Returns:
            dict: pandas dataframe with additional column for analysed data 
        """
        self._do_analysis(latest=with_latest_minute)
        return self.ohlc
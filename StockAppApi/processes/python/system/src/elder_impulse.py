import pandas

from StockAppApi.processes.python.system.base.system import System
from StockAppApi.base.python.src.yaml_parser import read_config
from StockAppApi.processes.python.talib.src.aggregator import Aggregator

class ElderImpulse(System):
    def __init__(self, indicator_config_file, selected_stocks_config_file, parameter:str, name="Elder") -> None:
        """The ElderImpulse system implementation. Search amonf the list of selected
        stocks, the trends associated and the indicate what kind of trade is 
        allowed in the current situation.
        
        Here, we have a fast ema EMA13 and macdhist as the basic constituents of 
        this indicator. When EMA13 both weekly and dailys slopes are positive
        and MACDHIST both weekly and dailies are positive we set the trend as bullish
        and also similarly the bearish trend is set. In short if the cumulative 
        of slopes is +ve it is bullish, -ve it is bearish and 0 means there is not
        much trend.

        Args:
            name (_type_): _description_ name of system may depend on the parameter passed
            selected_stocks_config_file (_type_): list of selected stocks
            parameter (str): message string defining the parameter for the system.
                e.g. elder --ema_window 13 --ema_n 100 --macd_fast_period 13 
                macd_slow_period 26 macd_signal_period 9 --macdhist_n 20
                
                A shorter version for default setup of parameter is
                e.g. elder. This sets the window to default values.
        """
        super().__init__(indicator_config_file, selected_stocks_config_file=selected_stocks_config_file, 
                         parameter=parameter, name=name)
        self.talib_aggregator = Aggregator(self.indicator_config_file)
    
    def execute(self) -> dict:
        """Execute the Elder impulse system and get result as pandas dataframe. 
        Check ema and macd slopes and which indicate the trend for the stock.
        The parameter is passed as a user string which is parsed to extract the 
        required information to set up this system.
        """
        cols= ['stock', 'ema_day_slope', 'ema_week_slope', 'macd_hist_day_slope', 
               'macd_hist_week_slope', 'ema_action', 'machdhist_action', 'trend']
        impulse_df = pandas.DataFrame(columns=cols)
        
        ema_window = int(self.parameter.get("ema_window", 13))
        ema_n = int(self.parameter.get("ema_n", 100))
        macd_fast_period = int(self.parameter.get("macd_fast_period", 13))
        macd_slow_period = int(self.parameter.get("macd_slow_period", 26))
        macd_signal_period = int(self.parameter.get("macd_signal_period", 9))
        macdhist_n = int(self.parameter.get("macdhist_n", 20))
        try:
            for stock in read_config(self.selected_stocks_config_file)['stock']:
                ema_day_query = f'select --stock {stock} --interval day | slope \
                --indicator ema --window {ema_window} --condition n={ema_n}'
                ema_day_query_slope = self.talib_aggregator.get_analysis(ema_day_query)['result']['slope']
                ema_day_query_result = 1 if ema_day_query_slope > 0 else -1
                
                ema_week_query = f'select --stock {stock} --interval week | slope \
                --indicator ema --window {ema_window} --condition n={int(ema_n*0.2)}' # a week is 5 times a day. ie. there are 5 days in a week
                ema_week_query_slope = self.talib_aggregator.get_analysis(ema_week_query)['result']['slope']
                ema_week_query_result = 1 if ema_week_query_slope > 0 else -1
                
                macdhist_day_query = f'select --stock {stock} --interval day | \
                slope --indicator macdhist --fastperiod {macd_fast_period} --slowperiod {macd_slow_period} \
                --signalperiod {macd_signal_period} --condition n={macdhist_n}'
                macdhist_day_query_slope = self.talib_aggregator.get_analysis(macdhist_day_query)['result']['slope']
                macdhist_day_query_result = 1 if macdhist_day_query_slope > 0 else -1
                
                macdhist_week_query = f'select --stock {stock} --interval week | \
                slope --indicator macdhist --fastperiod {macd_fast_period} --slowperiod {macd_slow_period} \
                --signalperiod {macd_signal_period} --condition n={int(macdhist_n * 0.2)}'
                macdhist_week_query_slope = self.talib_aggregator.get_analysis(macdhist_week_query)['result']['slope']
                macdhist_week_query_result = 1 if macdhist_week_query_slope > 0 else -1
                
                ema_impulse = ema_day_query_result + ema_week_query_result
                macd_impulse = macdhist_day_query_result + macdhist_week_query_result
                trend = "no trend"
                if ema_impulse + macd_impulse > 0:
                    trend = "bullish"
                elif ema_impulse + macd_impulse < 0:
                    trend = "bearish"
                    
                res = pandas.Series([stock, ema_day_query_slope, ema_week_query_slope, 
                                    macdhist_day_query_slope, macdhist_week_query_slope,
                                    ema_impulse, macd_impulse, trend], index=cols)
                impulse_df = pandas.concat([impulse_df, res.to_frame().T], ignore_index=True)
            return self._result(status=True, result=impulse_df)
        except Exception as e:
            return self._result(status=False, result=None)
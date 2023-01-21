import pandas
import numpy
from scipy.stats import linregress

from StockAppApi.processes.python.system.base.system import System, RetVal

class ElderImpulse(System):
    def __init__(self, indicator_config_file, selected_stocks_config_file, parameter:dict, command_handler: object, name="Elder") -> None:
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
                e.g. elder --window 13 --n 100 --macd_fast_period 13 
                macd_slow_period 26 macd_signal_period 9
                
                A shorter version for default setup of parameter is
                e.g. elder. This sets the window to default values.
        """
        super().__init__(indicator_config_file, selected_stocks_config_file=selected_stocks_config_file, 
                         parameter=parameter, command_handler=command_handler, name=name)
    
    def execute(self) -> RetVal:
        """Execute the Elder impulse system and get result as pandas dataframe
        with its string representation. Check ema and macd slopes and which 
        indicate the trend for the stock. The parameter is read from the query 
        string and converted into a property dict parameter.
        """
        cols= ['stock', 'ema_day_slope', 'ema_week_slope', 'macd_hist_day_slope', 
               'macd_hist_week_slope', 'ema_action', 'machdhist_action', 'trend']
        impulse_df = pandas.DataFrame(columns=cols)
        errors = ""
        for stock in self.selected_stocks_config['stock']:
            try:
                # get slope of last n data points of ema<window>.
                ema_day_query = f'talibquery --ticker {stock} --interval day --do get \
                --indicator ema --window {self.parameter["window"]} --n {self.parameter["n"]}'
                ema = self.command_handler.execute(ema_day_query, is_rest=False).obj['ema']
                slope_ema_day, _, _, _, _ = linregress(numpy.arange(0, ema.shape[0], 1), ema)
                
                ema_week_query = f'talibquery --ticker {stock} --interval week --do get \
                --indicator ema --window {self.parameter["window"]} --n {self.parameter["n"] * 0.2}' # a week is 5 times a day. ie. there are 5 days in a week
                ema = self.command_handler.execute(ema_week_query, is_rest=False).obj['ema']
                slope_ema_week, _, _, _, _ = linregress(numpy.arange(0, ema.shape[0], 1), ema)
                
                macdhist_day_query = f'talibquery --ticker {stock} --interval day --do \
                get --indicator macdhist --fastperiod {self.parameter["macd_fast_period"]} \
                --slowperiod {self.parameter["macd_slow_period"]} --signalperiod \
                {self.parameter["macd_signal_period"]} --n {self.parameter["n"]}'
                macdhist = self.command_handler.execute(macdhist_day_query, is_rest=False).obj['macdhist']
                slope_macdhist_day, _, _, _, _ = linregress(numpy.arange(0, macdhist.shape[0], 1), macdhist) 

                macdhist_week_query = f'talibquery --ticker {stock} --interval week --do \
                get --indicator macdhist --fastperiod {self.parameter["macd_fast_period"]} \
                --slowperiod {self.parameter["macd_slow_period"]} --signalperiod \
                {self.parameter["macd_signal_period"]} --n {self.parameter["n"] * 0.2}'
                macdhist = self.command_handler.execute(macdhist_week_query, is_rest=False).obj['macdhist']
                slope_macdhist_week, _, _, _, _ = linregress(numpy.arange(0, macdhist.shape[0], 1), macdhist) 
                
                ema_impulse =  (1 if slope_ema_day > 0 else -1) + (1 if slope_ema_week > 0 else -1 )
                macd_impulse = (1 if slope_macdhist_day > 0 else -1) + (1 if slope_macdhist_week > 0 else -1)
                trend = "no trend"
                if ema_impulse + macd_impulse > 0:
                    trend = "bullish"
                elif ema_impulse + macd_impulse < 0:
                    trend = "bearish"
                    
                res = pandas.Series([stock, slope_ema_day, slope_ema_week, 
                                    slope_macdhist_day, slope_macdhist_week,
                                    ema_impulse, macd_impulse, trend], index=cols)
                impulse_df = pandas.concat([impulse_df, res.to_frame().T], ignore_index=True)

            except Exception as e:
                errors += e.args + "\n"
                continue
        return RetVal(obj=impulse_df, 
                      obj_as_str=impulse_df.to_string(max_rows=None, max_cols=None, index=False),
                      errors=errors)
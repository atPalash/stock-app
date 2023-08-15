import pandas
import numpy
from scipy.stats import linregress

from StockAppApi.processes.python.system.base.system import System, RetVal


class Stage2Scanner(System):
    def __init__(self, indicator_config_file, selected_stocks_config_file, parameter: dict, command_handler: object, name="Stage2Template") -> None:
        """A stock must meet all eight criteria to be deemed in a confirmed Stage 2
        uptrend.

        1. Stock price is above both the 150-day (30-week) and the 200-day (40-
        week) moving average price lines.
        2. The 150-day moving average is above the 200-day moving average.
        3. The 200-day moving average line is trending up for at least 1-month
        (preferably 4 to 5 months or longer).
        4. The 50-day (10-week moving average) is above both the 150-day and
        the 200-day moving averages.
        5. The current stock price is at least 25 percent above its 52-week low.
        (Many of the best selections will be 100 percent, 300 percent, or more
        above their 52-week low before they emerge from a healthy
        consolidation period and mount a large-scale advance).
        6. The current stock price is within at least 25 percent of its 52-week high
        (the closer to a new high the better).
        7. The relative strength (RS) ranking (as reported in Investor’s Business
        Daily) is no less than 70, but preferably in the 90s, which will generally
        be the case with the better selections. (Note: The RS line should not be
        in a strong downtrend. I like to see the RS line in an uptrend for at least
        6 weeks, preferably 13 weeks or more.)
        8. Current price is trading above the 50-day moving average as the stock is
        coming out of a base.

        Args:
            name (_type_): _description_ name of system may depend on the parameter passed
            selected_stocks_config_file (_type_): list of selected stocks
            parameter (str): message string defining the parameter for the system.
                e.g. stage2scanner

                A shorter version for default setup of parameter is
                e.g. stage2scanner. This sets the window to default values.
        """
        super().__init__(indicator_config_file, selected_stocks_config_file=selected_stocks_config_file,
                         parameter=parameter, command_handler=command_handler, name=name)

        self.commands = {
            'get': self.__get  # calls with all or list of tickers
        }

    def __get(self) -> RetVal:
        """Execute the Stage2 scanner and get result as pandas dataframe
        with its string representation. The parameter is read from the query 
        string and converted into a property dict parameter.

        Returns:
            RetVal: the impulse map {stock, bool}
        """

        cols = ['stock', 'latest_ma_50', 'slope_ma_50_day', 'latest_ma_150', 'slope_ma_150_day',
                'latest_ma_200', 'slope_ma_200_day', 'low_52_week', 'high_52_week', 'valid_code', 'valid']
        impulse_df = pandas.DataFrame(columns=cols)
        errors = ""
        for stock in self._get_indices() + self._get_tickers():
            try:
                # ohlc day of stock 
                ticker_ohlc_csv_path = f"{self.indicator_config['indicator']['data']['day']}/{self.parameter['ticker']}.csv"
                ticker_df = pandas.read_csv(ticker_ohlc_csv_path)

                def getMa(window):
                    """Calcualate MA and slope.

                    Args:
                        window (int): rolling window

                    Returns:
                        tuple: list of MA, slope 
                    """
                    query = f'talibquery --ticker {stock} --interval {self.parameter["interval"]} --do get --csv 0 \
                    --indicator {self.parameter["stage2scannertype"]} --window {window} --n {self.parameter["n"]} --latest {self.parameter["latest"]}'
                    ma_list = self.command_handler.execute(
                        query, is_rest=False).obj[self.parameter["stage2scannertype"]]
                    slope, _, _, _, _ = linregress(
                        numpy.arange(0, ma_list.shape[0], 1), ma_list)

                    return ma_list, slope

                # Moving averages.
                ma_50_day, slope_ma_50_day = getMa(50)
                ma_150_day, slope_ma_150_day = getMa(150)
                ma_200_day, slope_ma_200_day = getMa(200)
                
                # 52 week low 
                low_52_week = ticker_df['Low'].tail(52*5).min()
                # 52 week high
                high_52_week = ticker_df['High'].tail(52*5).max()
                
                def shift(condition, val, pos): 
                    if condition:
                        return val | (1 << pos), pos + 1
                    return val, pos + 1
                valid = 0
                pos = 0
                latest_price = ticker_df['Close'].iloc[-1]
                latest_ma_50 = ma_50_day.iloc[-1]
                latest_ma_150 = ma_150_day.iloc[-1]
                latest_ma_200 = ma_200_day.iloc[-1]
                
                valid, pos = shift(latest_price > latest_ma_150 and latest_price > latest_ma_200, valid, pos)
                valid, pos = shift(latest_ma_150 > latest_ma_200, valid, pos)
                valid, pos = shift(slope_ma_200_day > 0, valid, pos)
                valid, pos = shift(latest_ma_50 > latest_ma_150 and latest_ma_50 > latest_ma_200, valid, pos)
                valid, pos = shift(latest_price > (low_52_week + low_52_week * 0.25), valid, pos)
                valid, pos = shift(latest_price > (high_52_week - high_52_week * 0.25), valid, pos)
                valid, pos = shift(latest_price > latest_ma_50, valid, pos)
                
                res = pandas.Series([stock, latest_ma_50, slope_ma_50_day,
                                    latest_ma_150, slope_ma_150_day,
                                    latest_ma_200, slope_ma_200_day, 
                                    low_52_week, high_52_week, valid, valid==127], index=cols)
                impulse_df = pandas.concat(
                    [impulse_df, res.to_frame().T], ignore_index=True)

            except Exception as e:
                errors += f"{stock}->{e.args}\n"
                continue
        return RetVal(obj=impulse_df,
                      obj_as_str=impulse_df.to_string(
                          max_rows=None, max_cols=None, index=False),
                      errors=errors)

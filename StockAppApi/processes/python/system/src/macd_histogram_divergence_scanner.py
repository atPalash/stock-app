from StockAppApi.processes.python.system.base.system import System, RetVal
from StockAppApi.base.python.src.candle_plotter import plot
import pandas

class MacdHistogramDivergenceScanner(System):
    def __init__(self, indicator_config_file: str, selected_stocks_config_file: str,
                 parameter: dict, command_handler: object, name="") -> None:
        """Scan for divergence points for stocks/stock, plot them in ohlc. Divergence
        occur when the macdhist crosses the zero line from buttom or top.

        1. Bullish divergence - 
                        B
                        |
                        | |                    
                ---------------
                    | |     |
                    |       C
                    A
            if priceA > price C (new low) and macdhistA < machistC -> bullish divergence
        2. Bearish divergence -
                    A
                    |           C
                    | | |       | |
                    ------------------
                            | |
                            |
                            B
            if priceA < priceC and macdhistA > macdhistC -> bearish divergence

        e.g.                
        MACDDIVERGENCESCAN
        1. macdhistdivergencescan --ticker TCS --interval day --do get --window 20 --n 80 -> 
        perform divergence scan on day chart of TCS with a rolling window=20 and samples n=80
        2. macdhistdivergencescan --ticker all --interval week --do get --window 40 --n 60 ->
        perform divergence scan on week chart of all selected with a rolling window=40 and samples n=60

        Args:
            indicator_config_file (str): indicator configuration
            selected_stocks_config_file (str): selected stocks list
            parameter (dict): key-value pairs for setting up the query
            command_handler (object): to call other systems
            name (str, optional): Name of the query. Defaults to "".
        """
        super().__init__(indicator_config_file=indicator_config_file,
                         selected_stocks_config_file=selected_stocks_config_file,
                         parameter=parameter,
                         command_handler=command_handler,
                         name=name)

        self.commands = {
            'get': self.__get
        }

    def execute(self) -> RetVal:
        try:
            ret = self.commands[self.parameter['do']]()
            return RetVal(ret, "Check dataframe")
        except Exception as e:
            raise

    def __get(self) -> RetVal:
        errors = ""
        divergence_df = {}
        for ticker in self._get_tickers():
            try:
                macdhist_query = f'talibquery --ticker {ticker} --interval {self.parameter["interval"]} --do get \
                    --indicator macdhist --fastperiod {self.parameter["macd_fast_period"]} \
                    --slowperiod {self.parameter["macd_slow_period"]} --signalperiod \
                    {self.parameter["macd_signal_period"]} --n {self.parameter["n"]} --latest {self.parameter["latest"]} --window {self.parameter["window"]}'
                ret = self.command_handler.execute(macdhist_query).obj

                ret['macdhist_divergence'] = 0
                # here taking close as the price
                for i in range(ret.index.min(), ret.index.max() - self.parameter['window'], 1):
                    window = ret.loc[i:i+self.parameter['window']]
                    window_macdhist = window['macdhist']
                    window_macdhist_min = window_macdhist.min()
                    window_macdhist_max = window_macdhist.max()
                    
                    # Check if the data has divergence in the samples, ie machist values (oscillatro)
                    if window_macdhist_min<0 and window_macdhist_max>0:
                        window_macdhist_min_index = window_macdhist[window_macdhist==window_macdhist_min].index[0]
                        window_macdhist_max_index = window_macdhist[window_macdhist==window_macdhist_max].index[0]

                        # Check bullish divergence. The two mins must be on both sides
                        # of the zero-cross. Start with finding the first min on left of
                        # max.
                        if window_macdhist_min_index < window_macdhist_max_index:
                            sub_window = window.loc[window_macdhist_max_index:i+self.parameter['window']]
                            sub_window_macdhist = sub_window['macdhist']
                            sub_window_macdhist_min = sub_window_macdhist.min()
                            sub_window_macdhist_max = sub_window_macdhist.max()

                            # Check if we get second min after zero-cross. Second
                            # min on right of max
                            if sub_window_macdhist_min<0 and sub_window_macdhist_max>0:
                                sub_window_macdhist_min_index = sub_window_macdhist[sub_window_macdhist==sub_window_macdhist_min].index[0]

                                # check for divergence condition
                                priceA = window[self.parameter['ohlc']].loc[window_macdhist_min_index] 
                                priceC = window[self.parameter['ohlc']].loc[sub_window_macdhist_min_index] 
                                macdhistA = window_macdhist_min
                                macdhistC = sub_window_macdhist_min
                                if priceA > priceC and macdhistA < macdhistC:
                                    ret.loc[sub_window_macdhist_min_index, 'macdhist_divergence'] = 1
                        
                        # Check bearish divergence. The two maxs must be on both the
                        # sides of the zero-cross. First start with finding the 
                        # first max is left of min
                        if window_macdhist_min_index > window_macdhist_max_index:
                            sub_window = window.loc[window_macdhist_min_index:i+self.parameter['window']]
                            sub_window_macdhist = sub_window['macdhist']
                            sub_window_macdhist_min = sub_window_macdhist.min()
                            sub_window_macdhist_max = sub_window_macdhist.max()

                            # Check if we get second max after zero-cross. the 2nd 
                            # max is right of min.
                            if sub_window_macdhist_min<0 and sub_window_macdhist_max>0:
                                sub_window_macdhist_max_index = sub_window_macdhist[sub_window_macdhist==sub_window_macdhist_max].index[0]

                                # check for divergence condition
                                priceA = window[self.parameter['ohlc']].loc[window_macdhist_max_index] 
                                priceC = window[self.parameter['ohlc']].loc[sub_window_macdhist_max_index] 
                                macdhistA = window_macdhist_max
                                macdhistC = sub_window_macdhist_max
                                if priceA < priceC and macdhistA > macdhistC:
                                    ret.loc[sub_window_macdhist_max_index, 'macdhist_divergence'] = -1     
                divergence_df[ticker] = ret
            except Exception as e:
                # errors += e.args + '\n'
                continue
        return divergence_df
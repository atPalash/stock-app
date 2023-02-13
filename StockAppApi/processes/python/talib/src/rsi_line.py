from StockAppApi.processes.python.talib.base.indicator import Indicator
from StockAppApi.processes.python.yahoofinance.src.data_fetcher import download_historical_data

class RsiLine(Indicator):
    def __init__(self, ohlc, parameter, ticker:str, name="", type="") -> None:
        super().__init__(name=name, type=type, ticker=ticker, ohlc=ohlc, parameter=parameter)
        self.interval ={'day' :'1d', 'hour': '1h', 'week': '1wk'}
        self.periods = {'day' : '5y', 'hour': '2y', 'week': '10y'}
        
    def _do_analysis(self, latest=True):
        #index data
        index_ohlc, err = download_historical_data(tickers=self.parameter['index'], 
        interval=self.interval[self.parameter['interval']],
        period=self.periods[self.parameter['interval']], 
        as_csv=self.parameter['csv'],
        as_panda_df=self.parameter['panda'])
        
        desired_ohlc_index = index_ohlc[self.parameter['ohlc']].values
        desired_ohlc_ticker = self.ohlc[self.parameter['ohlc']].values
        min_len = min(len(desired_ohlc_index), len(desired_ohlc_ticker))
        self.ohlc = self.ohlc.tail(min_len)
        self.ohlc = self.ohlc.copy()
        strength_series = desired_ohlc_ticker[:min_len] / desired_ohlc_index[:min_len]
        strength_series = (strength_series - strength_series.min()) / (strength_series.max() - strength_series.min())
        self.ohlc.loc[:,'rsiline'] = strength_series
        return strength_series
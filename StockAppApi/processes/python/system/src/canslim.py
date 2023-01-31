import pandas
import numpy
from scipy.stats import linregress

from StockAppApi.processes.python.system.base.system import System, RetVal
from StockAppApi.processes.python.yahoofinance.src.data_fetcher import download_stock_stats

class CanslimData:
    def __init__(self, C, A, N, S, L, I, M) -> None:
        self.C = C
        self.A = A
        self.N = N
        self.S = S
        self.L = L
        self.I = I
        self.M = M

class Canslim(System):
    def __init__(self, indicator_config_file, selected_stocks_config_file, parameter:dict, command_handler: object, name="canslim") -> None:
        """C: Current quarterly earnings per share (EPS) have increased sharply 
        from the same quarter in the prior year. Generally, investors using 
        CANSLIM want EPS growth of over 20%, but the higher the better.
        A: Annual earnings increases over the last five years. Again, annual EPS
        growth should ideally be in excess of 20% over the last three to five years.    
        N: New products, management, or positive new events that push the company's 
        stock to new highs. This type of headline news can cause short-term excitement, 
        propelling a surge of optimism within the market and subsequent price appreciation.
        S: Scarce supply coupled with a strong appetite for a stock creates excess 
        demand and an environment in which share prices can soar. Companies acquiring 
        (re-purchasing) their own stock reduces market supply and can indicate an 
        expectation of increased demand along with insider confidence in the firm.
        L: Leader/Laggard stocks are preferred within the same industry. Use the relative 
        strength index (RSI) as a guide. The RSI is a momentum indicator that measures the 
        magnitude of price changes to determine whether the price of a stock or 
        asset is overbought or oversold.
        I: Pick stocks that have institutional sponsorship by a few institutions 
        with recent above-average performance. For example, this could be a recently 
        public company, still supported by a small handful of well-known private equity firms. 
        M - Determine market direction by reviewing market averages daily. A market 
        average measures the overall price level of a given market, as defined by a 
        specified group of stocks, such as the Dow Jones Industrial Average. 
        CANSLIM stocks tend to be over-performers in bull markets.

        Args:
            indicator_config_file (str): indicator configuration
            selected_stocks_config_file (str): selected stocks list
            parameter (dict): key-value pairs for setting up the query
            name (str, optional): _description_. Defaults to "canslim".
        """
        super().__init__(indicator_config_file, selected_stocks_config_file=selected_stocks_config_file, 
                         parameter=parameter, command_handler=command_handler, name=name)
        
        self.commands = {
            'get': self.__get
        }

    def execute(self) -> RetVal:
        try:
            ret = self.commands[self.parameter['do']]()
            return RetVal(ret)
        except Exception as e:
            raise
    
    def __get(self):
        canslim_dict = {}
        for ticker in self._get_tickers():
            try:
                rsiline_query = f'talibquery --ticker {ticker} --interval day --do get \
                    --indicator rsiline --window {self.parameter["window"]} --n 400 \
                    --panda 1'
                rsiline = self.command_handler.execute(rsiline_query, is_rest=False).obj['rsiline']
                ema_query = f'talibquery --ticker ^NSEI --interval day --do get \
                    --indicator ema --window 26 --n 100 --panda 1'
                ema = self.command_handler.execute(ema_query, is_rest=False).obj['ema']
                
                folder_path = self.indicator_config["indicator"]["fundamental"]
                quarterly_financials = pandas.read_csv(f'{folder_path}/{ticker}_quarterly_financials.csv', index_col=0, parse_dates=True)
                quarterly_balancesheet = pandas.read_csv(f'{folder_path}/{ticker}_quarterly_balancesheet.csv', index_col=0, parse_dates=True)
                financials = pandas.read_csv(f'{folder_path}/{ticker}_financials.csv', index_col=0, parse_dates=True)
                # institutional_holders = pandas.read_csv(f'{folder_path}/{ticker}_institutional_holders.csv')
                
                canslim = CanslimData(
                    C=quarterly_financials.loc['Basic EPS'], 
                    A=financials.loc['Basic EPS'], 
                    N=None, 
                    S=quarterly_balancesheet.loc['Ordinary Shares Number'], 
                    L=rsiline, 
                    I=None, 
                    M=ema)
                canslim_dict[ticker] = canslim
            except Exception as e:
                print(ticker, e.args)
                continue

        return canslim_dict


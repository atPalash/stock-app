from StockAppApi.processes.python.system.base.system import System, RetVal
from StockAppApi.processes.python.yahoofinance.src.data_fetcher import download_historical_data

class YahooFinance(System):
    def __init__(self, indicator_config_file: str, selected_stocks_config_file: str, 
                 parameter: dict, command_handler: object, name="") -> None:
        """Download the ohlc data from yahoo finance. Save it as csv or use the 
        pandas dataframe for further analysis.

        e.g. 
        DOWNLOAD
        1. yahoofinance --ticker TCS --interval day --do download --pandas 0  --csv 1 -> saves to csv, returns empty pandas dataframe
        2. yahoofinance --ticker TCS --interval day --do download --pandas 1  --csv 0 -> donot save to csv, returns pandas dataframe
        
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
            'download': self.__download
        }

        self.interval ={'day' :'1d', 'hour': '1h', 'week': '1wk'}
        self.periods = {'day' : '5y', 'hour': '2y', 'week': '10y'}
        
    def execute(self) -> RetVal:
        try:
            ret = self.commands[self.parameter['do']]()
            return RetVal(ret, "downloaded")
        except Exception as e:
            raise
        
    def __download(self) -> RetVal:
        try:
            tickers = []
            ticker = self.parameter['ticker']
            if ticker == "all":
                tickers = self.selected_stocks_config['stock']
            
            tickers = [ticker + '.NS' for ticker in tickers]
            df = download_historical_data(tickers=tickers,
                                    period=self.periods[self.parameter['interval']], 
                                    interval=self.interval[self.parameter['interval']],
                                    as_panda_df=self.parameter['panda'],
                                    as_csv=self.parameter['csv'],
                                    destination=self.indicator_config['indicator']['data'][self.parameter['interval']])
            return df
        except Exception as e:
            raise
            
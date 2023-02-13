from StockAppApi.processes.python.system.base.system import System, RetVal
from StockAppApi.processes.python.yahoofinance.src.data_fetcher import download_historical_data, download_stock_stats


class YahooFinance(System):
    def __init__(self, indicator_config_file: str, selected_stocks_config_file: str,
                 parameter: dict, command_handler: object, name="") -> None:
        """Download the ohlc data from yahoo finance. Save it as csv or use the 
        pandas dataframe for further analysis.

        e.g. 
        DOWNLOAD
        1. yahoofinance --ticker TCS --interval day --do get --pandas 0  --csv 1 -> saves to csv, returns empty pandas dataframe
        2. yahoofinance --ticker TCS --interval day --do get --pandas 1  --csv 0 -> donot save to csv, returns pandas dataframe

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
            'get': self.__get,
            'fundamentals': self.__get_fundamentals
        }

        self.interval = {'day': '1d', 'hour': '1h', 'week': '1wk'}
        self.periods = {'day': '5y', 'hour': '2y', 'week': '10y'}

    def __get(self) -> RetVal:
        """Used to download ohlc data as csv for all the selected stocks and indexes.
        If the pandas is passed as 1 then the dataframe returned contains all the 
        selected stocks grouped in a single dataframe.
        Returns:
            RetVal: containing error as useful data.
        """
        tickers = self._get_tickers()
        # Need to add NS to download stock ohlc from yahoo
        tickers = [f"{tick}.NS" for tick in tickers]
        # We will download index ohlc with every download. Maybe add logic later
        # to avoid this redundant calls
        for index in self.selected_stocks_config['index']:
            tickers.append(index)  # For index ohlc no need to add NS

        df, err = download_historical_data(tickers=tickers,
                                      period=self.periods[self.parameter['interval']],
                                      interval=self.interval[self.parameter['interval']],
                                      as_panda_df=self.parameter['panda'],
                                      as_csv=self.parameter['csv'],
                                      destination=self.indicator_config['indicator']['data'][self.parameter['interval']])
        
        return RetVal(obj=df, obj_as_str="pandas dataframe downloaded", errors=err)

    def __get_fundamentals(self) -> RetVal:
        """Used to download fundamentals as csv all the selected stocks

        Returns:
            RetVal: containing error as useful data.
        """
        tickers = self._get_tickers()
        # Need to add NS to download stock fundamentals from yahoo
        tickers = [f"{tick}.NS" for tick in tickers]

        error = download_stock_stats(tickers=tickers, destination=self.indicator_config['indicator']['fundamental'])
        
        # return None as retval object since no sense to return fundamentals dataframe of different sizes. Just download
        # and read later
        return RetVal(obj=None, obj_as_str="None downloaded as csv", errors=error)

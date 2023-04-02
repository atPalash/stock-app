import pandas
from StockAppApi.processes.python.system.interface.system_if import SystemIf, RetVal
from StockAppApi.base.python.src.yaml_parser import read_config

class System(SystemIf):
    def __init__(self, indicator_config_file:str, selected_stocks_config_file:str, 
                 parameter: dict, command_handler: object, name="") -> None:
        self.name = name
        self.selected_stocks_config = read_config(selected_stocks_config_file)
        self.indicator_config = read_config(indicator_config_file)
        self.parameter = self.__update_parameter_or_set_to_default(parameter=parameter)
        self.command_handler = command_handler
        
    def execute(self):
        try:
            ret = self.commands[self.parameter['do']]()
            return ret
        except Exception as e:
            raise
    
    def __update_parameter_or_set_to_default(self, parameter:dict) -> dict:
        parameters = {
            'condition': parameter.get('condition', ''),
            'csv': int(parameter.get('csv', '0')),
            'do': parameter.get('do', 'get'),
            'indicator': parameter.get('indicator', 'ema'),
            'interval': parameter.get('interval', 'day'),
            'index': parameter.get('index', '^NSEI'),
            'latest': int(parameter.get('latest', '0')),
            'macd_fast_period': int(parameter.get('macd_fast_period','13')),
            'macd_slow_period': int(parameter.get("macd_slow_period", '26')),
            'macd_signal_period': int(parameter.get("macd_signal_period", '9')),
            'n': int(parameter.get('n', '10')),
            'ohlc': parameter.get('ohlc', 'Close'),
            'panda': int(parameter.get('panda', '0')),
            'period': parameter.get('period', '1y'),
            'plot': int(parameter.get('plot', '0')),
            'save_plot': parameter.get('save_plot', ''),
            'ticker': parameter.get('ticker', 'all'),
            'window': int(parameter.get('window', '20')),
        }
        
        return parameters
    
    def __get_list_of_tickers(self, type:str) -> list:
        tickers = []
        ticker = self.parameter['ticker']
        all_tickers = self.selected_stocks_config[type]
        if ticker == "all":
            tickers = all_tickers
        else:
            for tick in ticker.split(','):
                if tick in all_tickers:
                    tickers.append(tick)
        tickers = [ticker.replace(" ", "") for ticker in tickers]
        return tickers

    def _get_tickers(self) ->list:
        return self.__get_list_of_tickers('stock')
    
    def _get_indices(self) -> list:
        return self.__get_list_of_tickers('index')
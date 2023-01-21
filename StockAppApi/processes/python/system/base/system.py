import pandas
from StockAppApi.processes.python.system.interface.system_if import SystemIf
from StockAppApi.base.python.src.yaml_parser import read_config

class RetVal:
    def __init__(self, obj, obj_as_str="", errors="") -> None:
        self.obj = obj
        self.obj_as_string = ""
        if obj_as_str == "":
            self.obj_as_string = str(obj)
        else:
            self.obj_as_string = obj_as_str
        self.errors = errors
class System(SystemIf):
    def __init__(self, indicator_config_file:str, selected_stocks_config_file:str, 
                 parameter: dict, command_handler: object, name="") -> None:
        self.name = name
        self.selected_stocks_config = read_config(selected_stocks_config_file)
        self.indicator_config = read_config(indicator_config_file)
        self.parameter = self.__update_parameter_or_set_to_default(parameter=parameter)
        self.command_handler = command_handler
        
    def execute(self) -> RetVal:
        pass
    
    def __update_parameter_or_set_to_default(self, parameter:dict) -> dict:
        parameters = {
            'condition': parameter.get('condition', ''),
            'csv': bool(parameter.get('csv', True)),
            'do': parameter.get('do', 'get'),
            'indicator': parameter.get('indicator', 'ema'),
            'interval': parameter.get('interval', 'day'),
            'latest': bool(parameter.get('latest', True)),
            'macd_fast_period': int(parameter.get('macd_fast_period','13')),
            'macd_slow_period': int(parameter.get("macd_slow_period", '26')),
            'macd_signal_period': int(parameter.get("macd_signal_period", '9')),
            'n': int(parameter.get('n', '10')),
            'ohlc': parameter.get('ohlc', 'Close'),
            'panda': bool(parameter.get('panda', True)),
            'ticker': parameter.get('ticker', 'all'),
            'window': int(parameter.get('window', '20')),
        }
        
        return parameters
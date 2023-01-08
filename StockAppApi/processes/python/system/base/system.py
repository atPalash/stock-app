import pandas
from StockAppApi.processes.python.system.interface.system_if import SystemIf
from StockAppApi.base.python.src.message_parser import parse_message

class System(SystemIf):
    def __init__(self, indicator_config_file:str, selected_stocks_config_file:str, 
                 parameter: str, name="") -> None:
        self.name = name
        self.selected_stocks_config_file = selected_stocks_config_file
        self.indicator_config_file = indicator_config_file
        self.parameter = parse_message(parameter)[0] # there will be no sub-command
        
    def execute(self) -> dict:
        pass
    
    def _result(self, status: bool, result: object) -> dict:
        ret = {
            "status" : status,
            "result": result
        }
        return ret
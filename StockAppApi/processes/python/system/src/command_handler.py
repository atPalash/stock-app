from StockAppApi.base.python.interface.commandHandlerIf import CommandHandlerIf, Response, get_commands_as_str
from StockAppApi.base.python.src.message_parser import parse_message
from StockAppApi.processes.python.system.src.elder_impulse import ElderImpulse
from StockAppApi.processes.python.system.src.gherkin_query import GherkinQuery
from StockAppApi.processes.python.system.src.talib_query import TalibQuery
from StockAppApi.processes.python.system.src.yahoo_finance import YahooFinance
from StockAppApi.processes.python.system.src.macd_histogram_divergence_scanner import MacdHistogramDivergenceScanner
from StockAppApi.processes.python.system.src.canslim import Canslim
from StockAppApi.processes.python.system.src.webserver import Webserver
from StockAppApi.processes.python.system.src.stage2_scanner import Stage2Scanner

class CommandHandler(CommandHandlerIf):
    def __init__(self, selected_stocks_yaml, indicator_config_yaml) -> None:
        super().__init__()
        self.commands = { 
            "elderimpulse" : ElderImpulse,
            "talibquery" : TalibQuery,
            "yahoofinance": YahooFinance,
            "macdhistdivergencescan": MacdHistogramDivergenceScanner,
            "canslim": Canslim,
            "webserver": Webserver,
            "stage2scan": Stage2Scanner,
            "gherkinquery": GherkinQuery
        }
        self.selected_stocks_yaml = selected_stocks_yaml
        self.indicator_config_yaml = indicator_config_yaml
        
    def execute(self, message: str, is_rest=False):
        try:
            arguments = parse_message(message=message) # there will be no sub-command
            # command the system for analysis
            system = self.commands[arguments['command']](self.indicator_config_yaml, 
                                                         self.selected_stocks_yaml, 
                                                         arguments,
                                                         self) # the same command handler will handle calls from this system module
            ret = system.execute()
            
            if is_rest:
                return Response(ret.obj, 200, ret.obj_as_string, True)
            return ret            
        except Exception as e:
            if is_rest:
                return Response("exception", 400, e.args, False)
            return ret

    def get_command_as_str(self) -> str:
        """Register the commands associated with this command handler to master
        server.

        Returns:
            str: list of supported commands
        """
        return get_commands_as_str(self.commands)

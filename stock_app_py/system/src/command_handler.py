import pandas
from stock_app_py.interface.commandHandlerIf import (
    CommandHandlerIf,
    Response,
    get_commands_as_str,
)

from stock_app_py.system.src.indicator_list import IndicatorList
from stock_app_py.system.src.options.interface import OptionInterface
from stock_app_py.system.src.ticker_event import TickerEvent
from stock_app_py.utility.src.yaml_parser import read_config
from stock_app_py.utility.src.message_parser import parse_message


class CommandHandler(CommandHandlerIf):
    def __init__(self, selected_stocks_yaml, indicator_config_yaml) -> None:
        from stock_app_py.system.src.gherkin.gherkin_generic_query import (
            GherkinGenericQuery,
        )
        from stock_app_py.system.src.statement_list import StatementList
        from stock_app_py.system.src.elder_impulse import ElderImpulse
        from stock_app_py.system.src.gherkin.gherkin_query import GherkinQuery
        from stock_app_py.system.src.rs_rating import RsRating
        from stock_app_py.system.src.talib_query import TalibQuery
        from stock_app_py.system.src.yahoo_finance import YahooFinance
        from stock_app_py.system.src.macd_histogram_divergence_scanner import (
            MacdHistogramDivergenceScanner,
        )
        from stock_app_py.system.src.canslim import Canslim
        from stock_app_py.system.src.webserver import Webserver
        from stock_app_py.system.src.stage2_scanner import Stage2Scanner
        from stock_app_py.system.src.nse_stock_list import NseStockList
        from stock_app_py.system.src.user_config import UserConfig
        from stock_app_py.system.src.user_login import UserLogin

        super().__init__()
        self.commands = {
            "elderimpulse": ElderImpulse,
            "talibquery": TalibQuery,
            "yahoofinance": YahooFinance,
            "macdhistdivergencescan": MacdHistogramDivergenceScanner,
            "canslim": Canslim,
            "webserver": Webserver,
            "stage2scan": Stage2Scanner,
            "gherkinquery": GherkinGenericQuery,
            "nsestocklist": NseStockList,
            "rsrating": RsRating,
            "statementlist": StatementList,
            "userconfig": UserConfig,
            "userlogin": UserLogin,
            "indicatorlist": IndicatorList,
            "tickerevent": TickerEvent,
            "options": OptionInterface,
        }
        self.selected_stocks_yaml = selected_stocks_yaml
        self.indicator_config_yaml = indicator_config_yaml

    def execute(self, message: str, is_rest=False, ticker_df=None):
        try:
            arguments = parse_message(message=message)  # there will be no sub-command
            # command the system for analysis
            system = self.commands[arguments["command"]](
                self.indicator_config_yaml, self.selected_stocks_yaml, arguments, self
            )  # the same command handler will handle calls from this system module
            ret = system.execute(ticker_df)

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

from StockAppApi.base.python.interface.commandHandlerIf import CommandHandlerIf, Response
from StockAppApi.base.python.src.message_parser import parse_message
from StockAppApi.processes.python.talib.src.aggregator import Aggregator

class CommandHandler(CommandHandlerIf):
    def __init__(self, selected_stocks, aggregator: Aggregator) -> None:
        super().__init__()
        self.commands = "select"
        self.selected_stocks = selected_stocks
        self.aggregator = aggregator
        
    def execute(self, message: str) -> Response:
        try:
            result = self.aggregator.get_analysis(message)
                # send for filter
            return Response(result, 200, "", True)
        except Exception as e:
            # Base::Src::Log::LogCritical(__FILE__, __LINE__, e.what());
            return Response("exception", 400, e.args, False)

    def get_command_as_str(self) -> str:
        return self.commands

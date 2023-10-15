from stock_app_py.interface.commandHandlerIf import (
    CommandHandlerIf,
    Response,
    get_commands_as_str,
)
from stock_app_py.utility.src.message_parser import parse_message
from stock_app_py.scheduler.src.rs_rating import RsRating
from stock_app_py.scheduler.src.yahoofinance import YahooScheduler
from stock_app_py.scheduler.src.stock_list import StockList


class CommandHandler(CommandHandlerIf):
    def __init__(
        self,
        indicator_config_file: str,
        selected_stocks_config_file: str,
        master_url: str,
    ) -> None:
        super().__init__()
        self.commands = {"start": self.__start, "stop": self.__stop}

        self.schedulers = {
            "yahoo": YahooScheduler(
                indicator_config_file=indicator_config_file,
                selected_stocks_config_file=selected_stocks_config_file,
                master_url=master_url,
            ),
            "stocklist": StockList(
                indicator_config_file=indicator_config_file,
                selected_stocks_config_file=selected_stocks_config_file,
                master_url=master_url,
            ),
            "rsrating": RsRating(
                indicator_config_file=indicator_config_file,
                selected_stocks_config_file=selected_stocks_config_file,
                master_url=master_url,
            ),
        }

        self.__start()

    def execute(self, message: str, is_rest=False):
        """Start / Stop scheduler

        Args:
            message (str): _description_

        Returns:
            Response: _description_
        """
        try:
            command = parse_message(message=message)
            self.commands[command["command"]]()

            if is_rest:
                return Response("Stopped schedulers", 200, "", True)
        except Exception as e:
            if is_rest:
                return Response("exception", 400, e.args, False)

    def get_command_as_str(self) -> str:
        return get_commands_as_str(self.commands)

    def __start(self):
        for key, scheduler in self.schedulers.items():
            print(f"starting {key}")
            scheduler.run()

    def __stop(self):
        for key, scheduler in self.schedulers.items():
            print(f"stopping {key}")
            scheduler.stop()

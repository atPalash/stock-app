from base.python.interface.commandHandlerIf import CommandHandlerIf, Response
from base.python.src.message_parser import parse_message
from processes.python.yahoofinance.src.dataFetcher import download_historical_data


class CommandHandler(CommandHandlerIf):
    def __init__(self, selected_stocks) -> None:
        super().__init__()
        self.commands = "download"
        self.selected_stocks = selected_stocks
        # period : str
        #     Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
        #     Either Use period parameter or use start and end
        # interval : str
        #     Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
        #     Intraday data cannot extend last 60 days
        self.destination_config = {'1d' : 'day', '1h': 'hour', '1wk': 'week'}
        self.period_config = {'1d' : '5y', '1h': '2y', '1wk': '10y'}

    def execute(self, message: str) -> Response:
        try:
            arguments = parse_message(message=message, parser_symbol="--")
            if (arguments["command"] == "download"):
                tickers = []
                stock_list = arguments['stock'].split(",")
                if len(stock_list) == 1 and stock_list[0] == "all":
                    tickers = self.selected_stocks
                else:
                    for stock in stock_list:
                        tickers.append(stock.trim())
                tickers = [tick + '.NS' for tick in tickers]
                interval = arguments.get('interval', '1d')
                period = arguments.get('period', self.period_config[interval])
                destination = arguments.get('destination', f'database/{self.destination_config[interval]}')
                result = download_historical_data(tickers=tickers,
                                                  period=period,
                                                  interval=interval,
                                                  as_panda_df=arguments.get('panda', True),
                                                  as_csv=arguments.get('csv', False),
                                                  destination=destination)
                return Response("downloaded", 200, "", True)
            else:
                # Base::Src::Log::LogError(__FILE__, __LINE__, message);
                return Response("", 405, "MethodNotAllowed", False)
        except Exception as e:
            # Base::Src::Log::LogCritical(__FILE__, __LINE__, e.what());
            return Response("exception", 400, e.args, False)

    def get_command_as_str(self) -> str:
        return self.commands

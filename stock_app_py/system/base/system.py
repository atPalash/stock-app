from datetime import datetime
from stock_app_py.system.interface.system_if import SystemIf
from stock_app_py.utility.src.path_helper import get_app_path
from stock_app_py.utility.src.yaml_parser import read_config


class System(SystemIf):
    def __init__(
        self,
        indicator_config_file: str,
        selected_stocks_config_file: str,
        parameter: dict,
        command_handler: object,
        name="",
    ) -> None:
        self.name = name
        self.selected_stocks_config_file = selected_stocks_config_file
        self.indicator_config_file = indicator_config_file
        self.selected_stocks_config = read_config(selected_stocks_config_file)
        self.indicator_config = read_config(indicator_config_file)
        self.parameter = self.__update_parameter_or_set_to_default(parameter=parameter)
        self.command_handler = command_handler

    def execute(self, ticker_df=None):
        try:
            self.parameter["ticker_df"] = ticker_df
            ret = self.commands[self.parameter["do"]]()
            return ret
        except Exception as e:
            raise

    def __update_parameter_or_set_to_default(self, parameter: dict) -> dict:
        parameters = {
            "condition": parameter.get("condition", ""),
            "csv": int(parameter.get("csv", "0")),
            "config_dir": parameter.get("config_dir", get_app_path("configuration")),
            "do": parameter.get("do", "get"),
            "database_dir": parameter.get("database_dir", get_app_path("database")),
            "date": parameter.get("date", datetime.now().strftime("%d-%b-%Y")),
            "gherkin": parameter.get("gherkin", ""),
            "indicator": parameter.get("indicator", "ema"),
            "indicator_setting": parameter.get(
                "indicator_setting", ""
            ),  # comma separated config
            "interval": parameter.get("interval", "day"),
            "index": parameter.get("index", "^NSEI"),
            "index_csv": parameter.get(
                "index_csv", "all-indices.csv"
            ),  # https://www.nseindia.com/market-data/live-market-indices
            "json": parameter.get("json", ""),
            "latest": int(parameter.get("latest", "0")),
            "macd_fast_period": int(parameter.get("macd_fast_period", "13")),
            "macd_slow_period": int(parameter.get("macd_slow_period", "26")),
            "macd_signal_period": int(parameter.get("macd_signal_period", "9")),
            "ma_type": int(parameter.get("ma_type", "0")),  # bb ma type
            "n": int(parameter.get("n", "10")),
            "ohlc": parameter.get("ohlc", "Close"),
            "panda": int(parameter.get("panda", "0")),
            "period": parameter.get("period", "1y"),
            "plot": int(parameter.get("plot", "0")),
            "save_plot": parameter.get("save_plot", ""),
            "ticker": parameter.get("ticker", "all"),
            "window": int(parameter.get("window", "20")),
            "stage2scannertype": parameter.get("stage2scannertype", "ma"),
            "std_deviation": float(
                parameter.get("std_deviation", 5)
            ),  # bb std deviation
            "ticker_df": parameter.get("ticker_df", None),
            "username": parameter.get("username", ""),
        }

        return parameters

    def __get_list_of_tickers(self, type: str) -> list:
        tickers = []
        ticker = self.parameter["ticker"]
        all_tickers = self.selected_stocks_config[type]
        if ticker == "all":
            tickers = all_tickers
        else:
            for tick in ticker.split(","):
                if tick in all_tickers:
                    tickers.append(tick)
        tickers = [ticker.replace(" ", "") for ticker in tickers]
        return tickers

    def _get_tickers(self) -> list:
        return self.__get_list_of_tickers("stock")

    def _get_indices(self) -> list:
        return self.__get_list_of_tickers("index")

    def get_list_of_tickers(self, type: str) -> list:
        return self.__get_list_of_tickers(type=type)

import pandas

from stock_app_py.system.base.system import System
from stock_app_py.system.interface.system_if import RetVal
from stock_app_py.talib.src.bbands import Bbands
from stock_app_py.talib.src.ema import Ema
from stock_app_py.talib.src.macd import Macd
from stock_app_py.talib.src.rsi import Rsi
from stock_app_py.talib.src.rsi_line import RsiLine
from stock_app_py.talib.src.ma import Ma
from stock_app_py.talib.src.volatility import Volatility


class TalibQuery(System):
    def __init__(
        self,
        indicator_config_file: str,
        selected_stocks_config_file: str,
        parameter: dict,
        command_handler: object,
        name="",
    ) -> None:
        """Get the result of analysis from the indicators as a dataframe with ohlc
        and added columns to indicate the indicator results.

        e.g.
        GET
        1. talibquery --ticker TCS --interval day --do get --indicator ema : get the list of ema
        3. talibquery --ticker TCS --interval day --do get --indicator ema --n 1 --latest 1 (get the latest ema with latest minute data included)
        4. talibquery --ticker TCS --interval day --do get --indicator ema --n 10 --latest 1 (get the last 10 ema with latest minute data included)
        WHERE
        1. talibquery --ticker TCS --interval hour --do where --indicator ema --window 20 --condition value>1000 --latest 1

        Args:
            indicator_config_file (str): indicator configuration
            selected_stocks_config_file (str): selected stocks list
            parameter (dict): key-value pairs for setting up the query
            name (str, optional): Name of the query. Defaults to "".
        """
        super().__init__(
            indicator_config_file=indicator_config_file,
            selected_stocks_config_file=selected_stocks_config_file,
            parameter=parameter,
            command_handler=command_handler,
            name=name,
        )
        self.indicators = {
            "ema": Ema,
            "macd": Macd,
            "macdhist": Macd,
            "macdsignal": Macd,
            "rsi": Rsi,
            "rsiline": RsiLine,
            "ma": Ma,
            "atr": Volatility,  # TODO rename
            "bbands": Bbands,
            "upperbband": Bbands,
            "lowerbband": Bbands,
            "middlebband": Bbands,
        }

        self.commands = {
            "get": self.__get,  # call with single ticker
            "where": self.__where,  # call with single ticker
        }

    def __call_indicator(self) -> pandas.DataFrame:
        ticker_df = self.parameter.get("ticker_df")
        if ticker_df is None:
            ticker_ohlc_csv_path = f"{self.indicator_config['indicator']['data'][self.parameter['interval']]}/{self.parameter['ticker']}.csv"
            ticker_df = pandas.read_csv(ticker_ohlc_csv_path)
        indicator = self.indicators[self.parameter["indicator"]](
            ohlc=ticker_df, parameter=self.parameter, ticker=self.parameter["ticker"]
        )
        return indicator.get_result_df(self.parameter.get("latest", False))

    def __get(self) -> RetVal:
        try:
            df = self.__call_indicator()
            return RetVal(
                obj=df.tail(self.parameter["n"]),
                obj_as_str=df.tail(self.parameter["n"]).to_string(
                    max_rows=None, max_cols=None, index=False
                ),
                errors="",
            )
        except Exception as e:
            return RetVal(
                obj=None,
                obj_as_str="ERROR",
                errors=f"{self.parameter['ticker']}->{e.args}",
            )

    def __where(self) -> RetVal:
        """Search in dataframe where the condition is valid and return (NEEDS UPDATE)

        Returns:
            _type_: result of query: pandas dataframe
        """
        try:
            df = self.__call_indicator()
            df_query = df.query(self.parameter["condition"])
            return RetVal(obj=df_query, obj_as_str="pandas dataframe", errors="")
        except Exception as e:
            return RetVal(
                obj=None,
                obj_as_str="ERROR",
                errors=f"{self.parameter['ticker']}->{e.args}",
            )

    def debug(self):
        return self.__get()


if __name__ == "__main__":
    from stock_app_py.system.src.command_handler import CommandHandler
    from stock_app_py.utility.src.path_helper import get_app_path

    indicator_config_yaml = get_app_path("indicator.yaml")
    selected_stocks_yaml = get_app_path("selected_stocks.yaml")
    commandHandler = CommandHandler(
        selected_stocks_yaml, indicator_config_yaml=indicator_config_yaml
    )
    yf = TalibQuery(
        indicator_config_file=indicator_config_yaml,
        selected_stocks_config_file=selected_stocks_yaml,
        parameter={
            "indicator": "upperbband",
            "do": "get",
            "ticker": "TATAMOTORS",
            "window": 20,
        },
        command_handler=commandHandler,
        name="",
    )
    # https://www.niftyindices.com/IndexConstituent/ind_niftyautolist.csv
    # https://www.niftyindices.com/IndexConstituent/nifty_low_Volatility50_Index.csv
    # https://www.niftyindices.com/IndexConstituent/ind_niftyoilgaslist.csv
    # javascript:;
    data = yf.debug()
    print(data.obj)

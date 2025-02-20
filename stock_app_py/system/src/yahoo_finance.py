from datetime import datetime
import pandas
from stock_app_py.utility.src.json_helper import read_json
from stock_app_py.utility.src.path_helper import get_app_path
from stock_app_py.utility.src.yaml_parser import read_config
from collections import OrderedDict

from stock_app_py.system.base.system import System
from stock_app_py.system.interface.system_if import RetVal
from stock_app_py.yahoofinance.src.data_fetcher import (
    download_historical_data,
    download_stock_stats,
)


class YahooFinance(System):
    def __init__(
        self,
        indicator_config_file: str,
        selected_stocks_config_file: str,
        parameter: dict,
        command_handler: object,
        name="",
    ) -> None:
        """Download the ohlc data from yahoo finance. Save it as csv or use the
        pandas dataframe for further analysis.

        e.g.
        DOWNLOAD
        1. yahoofinance --ticker TCS --interval day --do get --pandas 0  --csv 1 -> saves to csv, returns empty pandas dataframe
        2. yahoofinance --ticker TCS --interval day --do get --pandas 1  --csv 0 -> donot save to csv, returns pandas dataframe

        Args:
            indicator_config_file (str): indicator configuration
            selected_stocks_config_file (str): selected stocks list
            parameter (dict): key-value pairs for setting up the query
            command_handler (object): to call other systems
            name (str, optional): Name of the query. Defaults to "".
        """
        super().__init__(
            indicator_config_file=indicator_config_file,
            selected_stocks_config_file=selected_stocks_config_file,
            parameter=parameter,
            command_handler=command_handler,
            name=name,
        )

        self.commands = {
            "get": self.__get,
            "fundamentals": self.__get_fundamentals,
            "financials": self.__get_financials,
            "ohlc": self.__get_ohlc,
        }
        # 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
        self.interval = {
            "minute": "1m",
            "minute5": "5m",
            "minute15": "15m",
            "minute30": "30m",
            "day": "1d",
            "hour": "1h",
            "week": "1wk",
            "month": "1mo",
        }
        # 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
        self.periods = {
            "minute": "5d",
            "minute5": "1mo",
            "minute15": "1mo",
            "minute30": "1mo",
            "day": "5y",
            "hour": "2y",
            "week": "10y",
            "month": "10y",
        }
        # 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
        self.duration = {
            "minute": 1,
            "minute5": 5,
            "minute15": 15,
            "minute30": 30,
            "day": 1440,
            "hour": 60,
            "week": 10080,
            "month": 40320,
        }

    def __get(self) -> RetVal:
        """Used to download ohlc data as csv for all the selected stocks and indexes.
        If the pandas is passed as 1 then the dataframe returned contains all the
        selected stocks grouped in a single dataframe.
        Returns:
            RetVal: containing error as useful data.
        """
        tickers = self._get_tickers()
        # Need to add NS to download stock ohlc from yahoo
        tickers = [f"{tick}.NS" for tick in tickers]

        # indices = self._get_indices()
        # tickers = tickers + indices

        df, err = download_historical_data(
            tickers=tickers,
            period=self.periods[self.parameter["interval"]],
            interval=self.interval[self.parameter["interval"]],
            as_panda_df=self.parameter["panda"],
            as_csv=self.parameter["csv"],
            destination=self.indicator_config["indicator"]["data"][
                self.parameter["interval"]
            ],
            version="v1",
        )

        return RetVal(obj=df, obj_as_str="pandas dataframe downloaded", errors=err)

    def __get_fundamentals(self, debug_tickers: list = []) -> RetVal:
        """Used to download fundamentals as csv all the selected stocks. Index don't have
        any fundamental data as a whole.

        Returns:
            RetVal: containing error as useful data.
        """
        if len(debug_tickers) == 0:
            tickers = self._get_tickers()
        else:
            tickers = debug_tickers
        # Need to add NS to download stock fundamentals from yahoo
        tickers = [f"{tick}.NS" for tick in tickers]

        error = download_stock_stats(
            tickers=tickers,
            destination=self.indicator_config["indicator"]["fundamental"],
        )

        # return None as retval object since no sense to return fundamentals dataframe of different sizes. Just download
        # and read later
        return RetVal(obj=None, obj_as_str="None downloaded as csv", errors=error)

    def __get_financials(self) -> RetVal:
        """Read the financials json and clean it and return

        Returns:
            RetVal: Return object containing a dictionary of financial statement
        """
        try:
            ret = {}
            financials = read_config(
                f'{self.parameter["database_dir"]}/fundamentals/{self.parameter["ticker"]}.json'
            )
            for statementType, statements in financials.items():
                temp = {}
                for data in statements:
                    for date, statement in data.items():
                        temp[datetime.strptime(date, "%Y-%m-%d")] = statement
                ret[statementType] = dict(
                    sorted(temp.items())
                )  # sort by date.python dicts are not sorted
            return RetVal(
                obj=ret,
                obj_as_str=f'{self.parameter["ticker"]}: financials dict',
                errors="",
            )
        except Exception as e:
            raise

    def __get_ohlc(self) -> RetVal:
        """Read the ohlc csv and return

        Returns:
            RetVal: Return object containing a pandas dataframe of ohlc data
        """
        try:
            ticker_ohlc_csv_path = f'{self.indicator_config["indicator"]["data"][self.parameter["interval"]]}/{self.parameter["ticker"]}.csv'
            ticker_df = pandas.read_csv(ticker_ohlc_csv_path)

            return RetVal(
                obj=ticker_df,
                obj_as_str=f'{self.parameter["ticker"]}: financials dict',
                errors="",
            )
        except Exception as e:
            raise

    def get_intervals_duration(self) -> list:
        return self.duration

    def read_ohlc(self, interval: str, ticker: str) -> RetVal:
        self.parameter["interval"] = interval
        self.parameter["ticker"] = ticker
        return self.__get_ohlc()

    def debug_get(self):
        return self.__get_ohlc().obj


if __name__ == "__main__":
    configFolder = "stock-app/configuration/"
    indicator_config_yaml = get_app_path("indicator.yaml")
    selected_stocks_yaml = get_app_path("selected_stocks.yaml")
    yf = YahooFinance(
        indicator_config_file=indicator_config_yaml,
        selected_stocks_config_file=selected_stocks_yaml,
        parameter={"interval": "minute5", "panda": 1, "ticker": "ADANIPORTS"},
        command_handler=None,
        name="",
    )
    data = yf.debug_get()
    print(data)

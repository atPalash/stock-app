import os
import re
import subprocess
import pandas
import csv

from stock_app_py.utility.src.csv_checker import is_csv_html
from stock_app_py.utility.src.path_helper import get_app_path
from stock_app_py.utility.src.yaml_parser import read_config, save_config
from stock_app_py.system.base.system import System
from stock_app_py.system.interface.system_if import RetVal


class TickerEvent(System):
    def __init__(
        self,
        indicator_config_file: str,
        selected_stocks_config_file: str,
        parameter: dict,
        command_handler: object,
        name="",
    ) -> None:
        """Download the events from nse. Updated the selected stock config

        e.g. tickerevent --do get
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
        }

    def __get(self) -> RetVal:
        """Return dict with selected stocks.
        Returns:
            RetVal: selected stock config
        """
        df = pandas.read_csv(get_app_path("CF-Event-equities.csv"))
        df.columns = df.columns.str.replace(" \n", "", regex=True)
        return RetVal(
            obj=df.to_dict(orient="records"), obj_as_str="pandas_df", errors=""
        )

    def debug(self):
        return self.__get()


if __name__ == "__main__":
    indicator_config_yaml = get_app_path("indicator.yaml")
    selected_stocks_yaml = get_app_path("selected_stocks.yaml")
    yf = TickerEvent(
        indicator_config_file=indicator_config_yaml,
        selected_stocks_config_file=selected_stocks_yaml,
        parameter={},
        command_handler=None,
        name="",
    )
    # https://www.niftyindices.com/IndexConstituent/ind_niftyautolist.csv
    # https://www.niftyindices.com/IndexConstituent/nifty_low_Volatility50_Index.csv
    # https://www.niftyindices.com/IndexConstituent/ind_niftyoilgaslist.csv
    # javascript:;
    data = yf.debug()
    print(data)

import os
import re
import subprocess
import time
import pandas
import csv

from stock_app_py.utility.src.path_helper import get_app_path
from stock_app_py.utility.src.yaml_parser import read_config
from stock_app_py.system.base.system import System
from stock_app_py.system.interface.system_if import RetVal
from stock_app_py.system.src.steps.given import aggregator as given_aggregator
from stock_app_py.system.src.steps.when import aggregator as when_aggregator
from stock_app_py.system.src.steps.then import aggregator as then_aggregator


class IndicatorList(System):
    def __init__(
        self,
        indicator_config_file: str,
        selected_stocks_config_file: str,
        parameter: dict,
        command_handler: object,
        name="",
    ) -> None:
        """Get list of supported indicators and signals. Each indicator has required parameters.
        Read the configuration from indicator.yaml and respond.

        e.g. indicatorlist --do get
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
        """Return dict with indicators and signals with configurations.
        Returns:
            RetVal: return object to be send to client
        """
        ret = None
        err = ""
        try:
            indicator_config = read_config(self.indicator_config_file)['indicator']['configurations']
            ret = {"ok": True, "indicators": indicator_config}
        except Exception as e:
            err = e.args[0]
        return RetVal(obj=ret, obj_as_str="dict of indicator configurations", errors=err)

    def debug(self):
        return self.__get()


if __name__ == "__main__":
    indicator_config_yaml = get_app_path("indicator.yaml")
    selected_stocks_yaml = get_app_path("selected_stocks.yaml")
    yf = IndicatorList(
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
    start_time = time.time()
    print(yf.debug().obj)
    print("--- %s seconds ---" % (time.time() - start_time))
    # print(data.obj)

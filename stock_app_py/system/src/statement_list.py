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


class StatementList(System):
    cached_statement = {"Given": [], "When": [], "Then": []}

    def __init__(
        self,
        indicator_config_file: str,
        selected_stocks_config_file: str,
        parameter: dict,
        command_handler: object,
        name="",
    ) -> None:
        """Read the statement regex supported by given, when, then. Add all possible
        combination to config.yaml. This list of statements is fetched by the client
        to show suggestion.

        e.g. statementlist --do get, statementlist --do update
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
            "update": self.__update,
        }
        # self.statements = []
        self.statement_map = {"Given": [], "When": [], "Then": []}

    def __get(self) -> RetVal:
        """Return dict with regex and it's possible statements.
        Returns:
            RetVal: return object to be send to client
        """
        if len(StatementList.cached_statement["Given"]) == 0:
            self.__update()
            StatementList.cached_statement = self.statement_map
        return RetVal(
            obj=StatementList.cached_statement,
            obj_as_str="list of regex and its statements",
            errors="",
        )

    def __update(self) -> RetVal:
        """Update the regex and its statements."""
        regex_dict = {}

        def make_regex_dict(steps: dict, stepType: str):
            for regex, val in steps.items():
                regex_dict[regex] = {
                    "type": stepType,
                    "variables": val.variables,
                    "placeholders": val.placeholders,
                    "query_type": val.query_type.value,
                    "meta": val.meta,
                }

        make_regex_dict(given_aggregator.get_steps(), "given")
        make_regex_dict(when_aggregator.get_steps(), "when")
        make_regex_dict(then_aggregator.get_steps(), "then")

        def make_statement(regex: str, options: dict, position: int):
            """Recursion to create a list of strings containing different combination
            of the options/variables defined.

            eg. ^relative strength ([><=!]+) (\d+)$
                variables={
                    2: StepData.condition,
                    3: StepData.number,
                },
            Here, the placeholder are situated at index 2 & 3. The caller of this
            method calls with position 2 as the start position. Next, the placeholder
            are replaced by options.

            Args:
                regex (str): parent regex whose supported statements are to be computed
                options (dict): supported values of each regex plaeholder
                position (int): the current placeholder whose options are being checked.
            """
            sample_statement = ""
            split_statement = regex.replace("^", "").replace("$", "").split(" ")
            for i in range(len(split_statement)):
                if i in options:
                    sample_statement += options[i][0] + " "
                else:
                    sample_statement += split_statement[i] + " "
            return sample_statement.strip()

        for regx, values in regex_dict.items():
            # User queries for backtest for selected stock in context, not required
            # as an query statement.
            if "backtest" not in regx:
                val = values["variables"]
                placeholders = values["placeholders"]
                query_type = values["query_type"]
                meta = values["meta"]
                if len(val.keys()) > 0:
                    sample_statement = make_statement(
                        regex=regx, options=val, position=list(val.keys())[0]
                    )
                    self.statement_map[values["type"].capitalize()].append(
                        {
                            "regex": regx,
                            "variables": val,
                            "statements": sample_statement,
                            "placeholders": placeholders,
                            "query_type": query_type,
                            "meta": meta,
                        }
                    )

        # Return obj as None since there is currently no requirement to return the
        # entire list
        return RetVal(obj=None, obj_as_str="updated statements list", errors="")

    def debug(self):
        return self.__get()


if __name__ == "__main__":
    indicator_config_yaml = get_app_path("indicator.yaml")
    selected_stocks_yaml = get_app_path("selected_stocks.yaml")
    yf = StatementList(
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
    print(yf.debug())
    print("--- %s seconds ---" % (time.time() - start_time))
    # print(data.obj)

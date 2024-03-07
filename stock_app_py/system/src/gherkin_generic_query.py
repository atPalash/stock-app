import json
import multiprocessing
import time
import re

import pandas

from stock_app_py.system.base.system import System
from stock_app_py.system.interface.system_if import RetVal
from stock_app_py.system.src.gherkin_query_ohlc_helper import GherkinQueryOhlcHelper
from stock_app_py.utility.src import gherkin_parser
import stock_app_py.system.src.steps.given.aggregator as given_aggregator
import stock_app_py.system.src.steps.then.aggregator as then_aggregator
import stock_app_py.system.src.steps.when.aggregator as when_aggregator
import stock_app_py.system.src.steps.given.given as given_step
import stock_app_py.system.src.steps.when.when as when_step
import stock_app_py.system.src.steps.then.then as then_step
from stock_app_py.system.src.steps import common
from stock_app_py.system.src.steps.common import PipeType
from stock_app_py.utility.src.path_helper import get_app_path
from stock_app_py.utility.src.yaml_parser import read_config


class GherkinGenericQuery(System):
    def __init__(
        self,
        indicator_config_file: str,
        selected_stocks_config_file: str,
        parameter: dict,
        command_handler: object,
        name="",
    ) -> None:
        """Get the result of gherkin query. Go through all the scenarios and make
        further queries to the indicators based on the steps then return the result.
        Creates a pandas dataframe which is pushed to each step and edited based on
        step logic. The idea is the steps don't return their results instead write
        directly to a common pandas.Dataframe.

        Generally the given steps create the ticker list, followed by when which
        creates the user variable values and then is used to compute the logic given
        by user. Error in each step is added to error for easy reference.
        <-given->|<common>|<--------when--------->|<-----then------>|
        | ticker |  error | variable1 | variable2 | logic1 | logic2 |

        e.g.
        #1 create the stock list
        Given nifty100 stocks -> selects stocks
        * remove stocks under surveillance -> filters stocks
        #1 -------------------------------------> create a dict with ticker + ohlc data

        #2 create the logic variables
        When let close = average in 5 day close --------|   user defined variables,
        * let ma150 = latest in 1 day close ma 150      |   updates the df from given
        * let ma200 = latest in 5 day close ma 200      |-->with columns as user defined
        * let atr = latest in 1 day close atr 14 -------|   variable name
        #2 -------------------------------------> create a dict with ticker + ohlc data + user variables

        #3 execute the logic
        Then get tickers with abs(ema20 - ema10) > atr * 1.5 -> user custom logic to be checked
        * get tickers with ema10 > ema20 -> user custom logic, if last this is PIPED with previous then
        #3 -------------------------------------> create a dict with ticker + ohlc data + user variables + logic of then

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

        self.commands = {
            "get": self.__get,  # call with single ticker
            # 'where': self.__where # call with single ticker
        }

        self.query_df_dict = {}
        self.query_df_json = {}
        self.steps = {"Given": {}, "When": {}, "Then": {}}
        self.step_version = "v2"
        self.gherkin_ohlc = GherkinQueryOhlcHelper(
            indicator_config_file=indicator_config_file,
            selected_stocks_config_file=indicator_config_file,
            parameter={},
            command_handler=None,
            name="",
        )

        def add_steps(supported_steps, step_type: str):
            for regex, func in supported_steps.items():
                self.steps[step_type][regex] = func

        add_steps(given_aggregator.get_steps(), "Given")
        add_steps(when_aggregator.get_steps(), "When")
        add_steps(then_aggregator.get_steps(), "Then")

    def fetch_gherkin_ohlc(self, groups, tickers) -> dict:
        for interval in self.gherkin_ohlc.get_intervals():
            if interval in groups:
                return self.gherkin_ohlc.get_interval_map(
                    interval=interval, tickers=tickers
                )
        return {}

    def __get(self) -> RetVal:
        try:
            check = gherkin_parser.parse(gherkin_string=self.parameter["gherkin"])
            conjunction_keyword = ["And", "*"]
            # scenario_results = {}
            for scenario in check["scenarios"]:
                query_df = pandas.DataFrame(columns=["ticker", "error"])
                current_keyword = ""
                for step in check["scenarios"][scenario]:
                    try:
                        errors = ""
                        keyword = step["keyword"].strip()
                        step_text = step["text"]
                        regex_steps = []
                        if keyword in conjunction_keyword:
                            regex_steps = self.steps[current_keyword]
                        else:
                            regex_steps = self.steps[keyword]
                        matched_step = common.get_matched_step(step_text, regex_steps)
                        if matched_step["matched"]:
                            pipe_type = matched_step["pipe"]
                            # First statement pipe is OR, i.e all result are allowed
                            if len(query_df) == 0:
                                pipe_type = PipeType.OR

                            if keyword == "Given" or (
                                current_keyword == "Given"
                                and keyword in conjunction_keyword
                            ):
                                # 1st step -> This step will create the list of stocks
                                # e.g. set the interval, selected stock etc.
                                current_keyword = "Given"
                                query_df = given_step.execute(
                                    matched_step,
                                    None,
                                    pipe_type,
                                    self.selected_stocks_config_file,
                                    self.indicator_config_file,
                                    step_version=self.step_version,
                                    query_df=query_df,
                                )

                            elif keyword == "When" or (
                                current_keyword == "When"
                                and keyword in conjunction_keyword
                            ):
                                # 2nd step -> compute the condition
                                # get the context from given above and generate result
                                # based on the condition
                                pipe_type = (
                                    PipeType.PASS
                                )  # Will not edit the pipe tickers
                                current_keyword = "When"
                                if "logic" in query_df.columns:
                                    query_df = query_df[query_df["logic"]]
                                ticker_df_map = self.fetch_gherkin_ohlc(
                                    matched_step["match"].groups(),
                                    query_df["ticker"].to_list(),
                                )
                                query_df = when_step.execute(
                                    matched_step,
                                    None,
                                    pipe_type,
                                    self.selected_stocks_config_file,
                                    self.indicator_config_file,
                                    step_version=self.step_version,
                                    query_df=query_df,
                                    tickers_df_dict=ticker_df_map,
                                )

                            elif keyword == "Then" or (
                                current_keyword == "Then"
                                and keyword in conjunction_keyword
                            ):
                                # Manipulate the query_df by adding the logic column
                                # for each step in then.
                                current_keyword = "Then"
                                query_df = then_step.execute(
                                    matched_step,
                                    None,
                                    pipe_type=pipe_type,
                                    step_version=self.step_version,
                                    query_df=query_df,
                                )
                            else:
                                raise Exception(
                                    f"Exception in matching keyword {keyword}"
                                )
                        else:
                            raise Exception(f"No matching steps found {step}")
                    except Exception as e:
                        errors += f"{step}->{e.args}\n"
                        raise Exception(errors)

                # Get the last column which is the combination of logic and get tickers
                # which satisfy.
                ret_tickers = query_df[query_df["logic"]]["ticker"].to_list()
                self.query_df_dict[scenario] = {
                    "query_df": query_df,
                    "tickers": ret_tickers,
                }
                self.query_df_json[scenario] = {
                    "query_df": query_df.to_json(orient='records'),
                    "tickers": ret_tickers,
                }
            return RetVal(
                obj={check["feature"]: self.query_df_dict},
                obj_as_str=json.dumps(self.query_df_json),
            )
        except Exception as e:
            return RetVal(
                obj=None,
                obj_as_str="ERROR",
                errors=f"{self.parameter['ticker']}->{e.args}",
            )


if __name__ == "__main__":
    from stock_app_py.system.src.command_handler import CommandHandler

    g_query = """Feature: v2
    I want to query to get a list of turtle S1 stocks
    Scenario: test
    Given nifty50 stocks
    When let rel_str = latest in 60 day close rs_rating
    Then get tickers with rel_str > 0.9
    When let atr = latest in 1 day close atr 14
    * let close = latest in 1 day close
    * let ma150 = latest in 1 day close ma 150
    * let ma200 = latest in 1 day close ma 200
    * let ma50 = latest in 1 day close ma 50
    * let rate_ma200 = rate in 60 day close ma 200
    * let wk_52low = minimum in 52 week close
    * let wk_52high = maximum in 52 week close
    Then let close_ma50 = close > ma50
    * let close_ma150 = close > ma150
    * let close_ma200 = close > ma200
    * let ma50_ma150 = ma50 > ma150
    * let ma50_ma200 = ma50 > ma200
    * let ma150_ma200 = ma150 > ma200
    * let uptrend200 = rate_ma200 > 0
    * let close_52wklow = close > 1.25 * wk_52low
    * let close_52wkhigh = close > 0.75 * wk_52high
    * get tickers with close_ma50 and close_ma150 and close_ma200 and ma50_ma150 and ma50_ma200 and ma150_ma200 and uptrend200 and close_52wklow and close_52wkhigh
    """
#     g_query = """Feature: v2
# I want to query to get a list of turtle S1 stocks
# Scenario: test
# Given stocks ABB, TCS
# When let rel_str = latest in 60 day close rs_rating
# Then get tickers with rel_str > 0.8
# When let atr14 = latest in 1 day close atr 14
# * let close = latest in 1 day close
# * let ema10 = latest in 1 day close ema 10
# * let ema20 = latest in 1 day close ema 20
# Then get tickers with (ema10 - ema20) < atr14 * 0.5
# """

    start = time.time()
    indicator_config_yaml = get_app_path("indicator.yaml")
    selected_stocks_yaml = get_app_path("selected_stocks.yaml")
    commandHandler = CommandHandler(
        selected_stocks_yaml, indicator_config_yaml=indicator_config_yaml
    )
    parser = GherkinGenericQuery(
        indicator_config_file=indicator_config_yaml,
        selected_stocks_config_file=selected_stocks_yaml,
        command_handler=commandHandler,
        parameter={"do": "get", "gherkin": g_query},
        name="",
    )

    check = parser.execute()
    check.obj["v2"]["test"]["query_df"].to_csv("query_df.csv", index=False)

    print(check.obj["v2"]["test"]["tickers"])
    print("elasped time", time.time() - start)

"""I want to query to get a list of turtle S1 stocks
Scenario: test
Given nifty50 stocks
* add stocks ABB
* add stocks MEDANTA, GLS, TCS
* remove stocks under surveillance
* remove stocks AXISBANK
* remove stocks MEDANTA
When let slope_ema10 = slope in 5 day close ema 10
* let ema20 = latest in 5 day close ema 20
Then get tickers with ema10 > ema20
"""

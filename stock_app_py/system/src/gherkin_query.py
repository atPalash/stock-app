import multiprocessing
import time
import re

from stock_app_py.system.base.system import System
from stock_app_py.system.interface.system_if import RetVal
from stock_app_py.utility.src import gherkin_parser
import stock_app_py.system.src.steps.given.aggregator as given_aggregator
import stock_app_py.system.src.steps.then.aggregator as then_aggregator
import stock_app_py.system.src.steps.when.aggregator as when_aggregator
import stock_app_py.system.src.steps.given.given as given_step
import stock_app_py.system.src.steps.when.when as when_step
import stock_app_py.system.src.steps.then.then as then_step
from stock_app_py.system.src.steps.common import GherkinQueryRet, PipeType
from stock_app_py.utility.src.path_helper import get_app_path


class GherkinQuery(System):
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
        Note: The Given and Then steps are implemented by this class, whereas the
        When are implemented by the individual indicators.

        e.g.
        gherkin --query
        Feature: Query
        I want to query to get a list of matches
        Scenario: filter for ema and ma
            Given all nifty 50 stocks
            When ema of window <window> is <condition> <rhs>
            And ma of window <window> is <condition> <rhs>
            Then get list of top 20 stocks

            Examples:
                | window    | condition     | rhs       |
                | 20        | >             | close     |
                | 60        | >             | close     |

        Scenario: check ema
            Given all nifty 50 stocks
            When ema of window 50 is > open
            Then get list of top 10 stocks

        Scenario: check ma
            Given all nifty 50 stocks
            When ma of window 100 is > high
            Then get list of top 10 stocks


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

        self.steps = {}

        def add_steps(supported_steps):
            for regex, func in supported_steps.items():
                self.steps[regex] = func

        add_steps(given_aggregator.get_steps())
        add_steps(when_aggregator.get_steps())
        add_steps(then_aggregator.get_steps())

    def __get_matched_step(self, rule: str):
        result = {"matched": False, "match": None, "func": None}
        for pattern, func in self.steps.items():
            match = re.search(pattern, rule)
            if match:
                result["matched"] = True
                result["match"] = match
                result["func"] = func
                break
        return result

    def __convertToBacktest(self, gherkin_query: str) -> dict:
        """Convert the gherkin query to backtest gherkin query. Ensure the keyword
        Backtest is in the top line.

        Args:
            gherkin_query (str): gherkin query string with Backtest in top line

        Returns:
            dict: converted steps
        """
        lines = gherkin_query.split("\n")
        backtest_ticker = lines[0].split(":")[1]
        query = "\n".join(lines[1:])
        check = gherkin_parser.parse(gherkin_string=query)
        conjunction_keyword = ["And ", "* "]
        for scenario in check["scenarios"]:
            current_keyword = ""
            for step in check["scenarios"][scenario]:
                keyword = step["keyword"]
                step_text = step["text"]
                if keyword == "Given " or (
                    current_keyword == "Given " and keyword in conjunction_keyword
                ):
                    step["text"] = f"stocks {backtest_ticker}"
                    current_keyword = "Given "
                elif keyword == "When " or (
                    current_keyword == "When " and keyword in conjunction_keyword
                ):
                    hard_coded_tick_count = 100
                    if "week" in step["text"]:
                        hard_coded_tick_count = 20
                    if "relative" in step["text"]:
                        hard_coded_tick_count = 5
                    step[
                        "text"
                    ] = f"backtest for last {hard_coded_tick_count} ticks | {step_text}"
                    current_keyword = "When "
                elif keyword == "Then " or (
                    current_keyword == "Then " and keyword in conjunction_keyword
                ):
                    step["text"] = f"get list of stocks with signals"
                    current_keyword = "Then "
        return check

    def __get(self) -> RetVal:
        try:
            check = None
            if "Backtest" in self.parameter["gherkin"]:
                check = self.__convertToBacktest(self.parameter["gherkin"])
            else:
                check = gherkin_parser.parse(gherkin_string=self.parameter["gherkin"])
            conjunction_keyword = ["And ", "* "]
            scenario_results = {}
            for scenario in check["scenarios"]:
                step_results = []
                for step in check["scenarios"][scenario]:
                    try:
                        errors = ""
                        keyword = step["keyword"]
                        step_text = step["text"]
                        matched_step = self.__get_matched_step(step_text)
                        step_result = GherkinQueryRet(
                            parent="",
                            type=keyword,
                            step=step_text,
                            errors="",
                            result=None,
                        )
                        if matched_step["matched"]:
                            pipe_type = PipeType.AND
                            if "remove" in step_text:
                                pipe_type = PipeType.NOT
                            elif "add" in step_text or len(step_results) == 0:
                                pipe_type = PipeType.OR

                            if keyword == "Given " or (
                                current_keyword == "Given "
                                and keyword in conjunction_keyword
                            ):
                                # 1st step -> read the context
                                # e.g. set the interval, selected stock etc.
                                current_keyword = "Given "
                                step_result.parent = (
                                    "" if keyword == "Given " else "given"
                                )
                                step_result.result = given_step.execute(
                                    matched_step,
                                    step_results[-1] if len(step_results) > 0 else None,
                                    pipe_type,
                                    self.selected_stocks_config_file,
                                    self.indicator_config_file,
                                )
                                step_results.append(step_result)
                            elif keyword == "When " or (
                                current_keyword == "When "
                                and keyword in conjunction_keyword
                            ):
                                # 2nd step -> compute the condition
                                # get the context from given above and generate result
                                # based on the condition
                                current_keyword = "When "
                                step_result.parent = (
                                    "" if keyword == "When " else "when"
                                )
                                step_result.result = when_step.execute(
                                    matched_step,
                                    step_results[-1] if len(step_results) > 0 else None,
                                    pipe_type,
                                    self.selected_stocks_config_file,
                                    self.indicator_config_file,
                                )
                                step_results.append(step_result)
                            elif keyword == "Then " or (
                                current_keyword == "Then "
                                and keyword in conjunction_keyword
                            ):
                                # 3rd step -> data presentation
                                current_keyword = "Then "
                                step_result.parent = (
                                    "" if keyword == "Then " else "then"
                                )
                                step_result.result = then_step.execute(
                                    matched_step,
                                    step_results,
                                    PipeType.PASS,
                                )
                                step_results.append(step_result)
                            else:
                                raise Exception(
                                    f"Exception in matching keyword {keyword}"
                                )
                        else:
                            raise Exception(f"No matching steps found {step}")
                    except Exception as e:
                        errors += f"{step}->{e.args}\n"
                        step_result["errors"] = errors
                        raise Exception(errors)
                scenario_results[scenario] = self.__convertToDict(step_results)
            return RetVal(
                obj={check["feature"]: scenario_results},
                obj_as_str="a dict of when given then result",
            )
        except Exception as e:
            return RetVal(
                obj=None,
                obj_as_str="ERROR",
                errors=f"{self.parameter['ticker']}->{e.args}",
            )

    def __convertToDict(self, step_results: list) -> list:
        ret = []
        for step in step_results:
            temp = vars(step)
            temp["result"] = vars(step.result)
            temp["result"]["pipe_type"] = step.result["pipe_type"].name
            ret.append(temp)
        return ret


if __name__ == "__main__":
    from stock_app_py.system.src.command_handler import CommandHandler

    g_query = """Backtest:ABB
Feature: test
I want to query to get a list of turtle S1 stocks      
Scenario: test
Given all stocks
When relative strength > 90 
* day close ma 50 < close
Then get list
"""

    start = time.time()
    indicator_config_yaml = get_app_path("indicator.yaml")
    selected_stocks_yaml = get_app_path("selected_stocks.yaml")
    commandHandler = CommandHandler(
        selected_stocks_yaml, indicator_config_yaml=indicator_config_yaml
    )
    parser = GherkinQuery(
        indicator_config_file=indicator_config_yaml,
        selected_stocks_config_file=selected_stocks_yaml,
        command_handler=commandHandler,
        parameter={"do": "get", "gherkin": g_query},
        name="",
    )

    check = parser.execute()
    print(check.obj["test"])
    print("elasped time", time.time() - start)

"""
Given stocks ASAHIINDIA, ASTRAZEN, BANKBARODA, BANKINDIA, BARBEQUE, CANBK, CENTRALBK,DBREALTY, DEN,EASEMYTRIP,FINEORG,GRAVITA,HEROMOTOCO,ICICIPRULI,IOB,MAHABANK,NESTLEIND,PNB,PSB,SBIN, SOUTHBANK,SUNTECK,TATAINVEST,TATAMOTORS,THYROCARE,TITAN,TVSMOTOR,UCOBANK,UNIONBANK,VARROC
When day close ma 50 < close
* day close ma 150 < close
* day close ma 200 < close
* day close ma 50 > day close ma 150
* day close ma 50 > day close ma 200
* day close ma 150 > day close ma 200
* day close ma 200 in uptrend for 60 days
* 1.25 of 52 week low < close
* 0.75 of 52 week high < close
Then get list of all match
Feature: Back test day turtle S1
    I want to query to backtest in stocks
    Scenario: backtest stocks
    Given nifty 100 stocks
    When backtest for last 100 ticks with signal color green | day close > close of last 55 ticks
    Then get list of stocks with signals
    Feature: Back test
    I want to query to backtest in stocks
    Scenario: backtest stocks
    Given nifty 50 stocks
    When backtest for last 100 ticks with signal color green | day close shows macd divergence with window 20 fastperiod 12 slowperiod 26 signalperiod 9 in last 40 ticks
    Then get list of stocks with signals
Feature: Stocks with MACD divergence
    I want to query to get a list of macd divergence stocks      
    Scenario: list stocks showing macd divergence
    Given nifty 50 stocks
    When day close shows macd divergence with window 20 in last 40 ticks
    Then get list of stocks with signals
    Feature: Query
    I want to query to get a list of matches      
        Scenario: filter for ema and ma 
        Given nifty 50 stocks
        When <interval> <ohlc source> <indicator> <window> <condition> <ohlc>
        And hour close ma 100 < hour open ma 20
        Then get list of top 20

        Examples:
        | interval  | ohlc source       | indicator     | window    | condition     | ohlc      |   
        | day       | close             | ema           | 20        | >             | open      |
        | week      | open              | ma            | 60        | >             | close     | 
        
        Scenario: check ema50
        Given nifty 100 stocks
        When week close ema 50 > open
        Then get list of top 10
        
        Scenario: check ema70
        Given nifty 200 stocks
        When week close ema 70 > day open ma 20
        Then get list of top 10
    """
"""
    g_query = 
    Feature: Query
    I want to query to get a list of matches      
        Scenario: filter for ema and ma 
        Given nifty 50 stocks
        When <interval> <ohlc source> <indicator> <window> <condition> <ohlc>
        And hour close ma 100 < hour open ma 20
        Then get list of top 20

        Examples:
        | interval  | ohlc source       | indicator     | window    | condition     | ohlc      |   
        | day       | close             | ema           | 20        | >             | open      |
        | week      | open              | ma            | 60        | >             | close     | 
        
        Scenario: check ema50
        Given nifty 100 stocks
        When week close ema 50 > open
        Then get list of top 10
        
        Scenario: check ema70
        Given nifty 200 stocks
        When week close ema 70 > close
        Then get list of top 10

    """

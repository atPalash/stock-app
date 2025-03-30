import time
import pandas

from stock_app_py.system.base.system import System
from stock_app_py.system.interface.system_if import RetVal
from stock_app_py.system.src.gherkin.gherkin_query_ohlc_helper import (
    GherkinQueryOhlcHelper,
)
from stock_app_py.utility.src import gherkin_parser
import stock_app_py.system.src.steps.given.aggregator as given_aggregator
import stock_app_py.system.src.steps.then.aggregator as then_aggregator
import stock_app_py.system.src.steps.when.aggregator as when_aggregator
import stock_app_py.system.src.steps.given.given as given_step
import stock_app_py.system.src.steps.when.when as when_step
import stock_app_py.system.src.steps.then.then as then_step
from stock_app_py.system.src.steps import common
from stock_app_py.system.src.steps.common import PipeType
from stock_app_py.utility.src.logger import get_logger
from stock_app_py.utility.src.path_helper import get_app_path
from stock_app_py.utility.src.yaml_parser import read_config

logger = get_logger(__name__)


class GherkinGenericQuery(System):
    def __init__(
        self,
        indicator_config_file: str,
        selected_stocks_config_file: str,
        parameter: dict,
        command_handler: object,
        gherkin_ohlc_helper: object = None,
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
        Given stocks from index nifty100 -> selects stocks
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
            name="",
        )

        self.commands = {
            "get": self.__get,  # call with single ticker
            # 'where': self.__where # call with single ticker
        }

        self.query_df_dict = {}
        self.query_df_json = {}
        self.steps = {"Given": {}, "When": {}, "Then": {}}
        self.step_version = "v2"
        self.gherkin_ohlc = (
            GherkinQueryOhlcHelper(
                indicator_config_file=indicator_config_file,
                selected_stocks_config_file=indicator_config_file,
                parameter={},
                command_handler=None,
                name="",
            )
            if gherkin_ohlc_helper == None
            else gherkin_ohlc_helper
        )
        self.query_tickers = []

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

    def get_tickers(self):
        return self.query_tickers

    # @profile
    def __get(self) -> RetVal:
        try:
            check = gherkin_parser.parse(gherkin_string=self.parameter["gherkin"])
            conjunction_keyword = ["And", "*"]

            # It is possible to have 1 scenario per query
            feature = check["feature"]
            scenario = next(iter(check["scenarios"]))
            # Make user name the scenario, unnamed scenario may causes issues
            if scenario != "" and feature == "v2":
                query_df = pandas.DataFrame(columns=["ticker", "error"])
                current_keyword = ""
                then_logic_names = []
                for step in check["scenarios"][scenario]:
                    try:
                        if query_df["error"].apply(lambda x: x != "").any():
                            print(
                                f"error in {query_df[query_df['error']!= '']['ticker']}"
                            )
                            query_df = query_df[query_df["error"] == ""]
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
                                # pipe_type = PipeType.OR  # Allow ticker to be add this if multiple given. TODO test
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
                                self.query_tickers = query_df["ticker"].tolist()

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
                                    # It seems we have filtered all the tickers just return
                                    if len(query_df) == 0:
                                        return RetVal(
                                            obj={scenario: None},
                                            obj_as_str={scenario: "None"},
                                            errors={
                                                "error": "Filtered out all tickers"
                                            },
                                        )
                                ticker_df_map = self.fetch_gherkin_ohlc(
                                    matched_step["match"].groups(),
                                    query_df["ticker"].to_list(),
                                )
                                # hack hack hack
                                for k in list(ticker_df_map.keys()):
                                    if ticker_df_map[k] is None:
                                        query_df = query_df[query_df["ticker"] != k]
                                        del ticker_df_map[k]
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
                                # add then list statement as logic
                                if "list" in matched_step["match"].string:
                                    then_logic_names.append(
                                        matched_step["match"].groups()[0]
                                    )
                            else:
                                logger.error(f"Exception in matching keyword {keyword}")
                                raise Exception(
                                    f"Exception in matching keyword {keyword}"
                                )
                        else:
                            logger.error(f"No matching steps found {step}")
                            raise Exception(f"No matching steps found {step}")

                    except Exception as e:
                        logger.error(f"{step} {e.args}")
                        errors += f"{step}->{e.args}\n"
                        raise Exception(errors)

                # Get the last column which is the combination of logic and get tickers
                # which satisfy.
                ret_tickers = []
                errors = ""
                ret_logic_tickers = {}
                if query_df["error"].values[0] != "":
                    errors = (
                        query_df["error"].values[0].split(":")[1]
                    )  # Assuming syntax errors
                elif "series" in query_df.columns:
                    # A series of data signifying condition check and indicator data
                    ret_tickers = query_df["ticker"][0]
                elif len(then_logic_names) > 0:
                    temp = set()
                    for logic in then_logic_names:
                        tickers = query_df[query_df[logic]]["ticker"].to_list()
                        temp.update(tickers)
                        ret_logic_tickers[logic] = tickers
                    ret_tickers = list(sorted(temp))
                else:
                    ret_tickers = query_df[query_df["logic"]]["ticker"].to_list()
                self.query_df_dict[scenario] = {
                    "query_df": query_df,
                    "tickers": ret_tickers,
                    "logic_tickers": ret_logic_tickers,
                    "errors": errors,
                }
                self.query_df_json[scenario] = "None"
                if errors == "":
                    self.query_df_json[scenario] = {
                        "query_df": (
                            query_df["series"][0].to_json(orient="records")
                            if "series" in query_df.columns
                            else query_df.to_json(orient="records")
                        ),
                        "tickers": ret_tickers,
                        "logic_tickers": ret_logic_tickers,
                        "errors": errors,
                    }
                return RetVal(
                    obj=self.query_df_dict,
                    obj_as_str=self.query_df_json,
                    errors={"error": errors},
                )
            else:
                return RetVal(
                    obj={scenario: None},
                    obj_as_str={scenario: "None"},
                    errors={"error": "Unnamed query are not allowed"},
                )
        except Exception as e:
            return RetVal(
                obj={scenario: None},
                obj_as_str={scenario: "None"},
                errors={"error": {"step": step["text"]}},
            )


if __name__ == "__main__":
    from stock_app_py.system.src.command_handler import CommandHandler

    g_query = """
Feature: v2
Scenario: test
Given stocks from index nifty50\n
* stocks from list ^NSEI, ^NSEBANK, ^NSMIDCP, NIFTY_MID_SELECT, NIFTY_FIN_SERVICE\n
When let ema10Change = rate in 20 samples of minute5 close ema 10\n
* let vwap10Change = rate in 20 samples of minute5 close vwap 10\n
* let vwapMax = maximum in 10 samples of minute5 close vwap 10\n
* let vwapMin = minimum in 10 samples of minute5 close vwap 10\n
* let emaMax = maximum in 10 samples of minute5 close ema 10\n
* let emaMin = minimum in 10 samples of minute5 close ema 10\n
* let ema10Day = latest in 1 samples of day close ema 10\n
* let close = latest in 1 samples of minute5 close\n
Then list bulls = tickers with ema10Change > 0 and vwap10Change > 0 and close > ema10Day * 0.99 and close < ema10Day * 1.01\n
* list bears = tickers with ema10Change < 0 and vwap10Change < 0 and close > ema10Day * 0.99 and close < ema10Day * 1.01\n
* list vwapCross = tickers with vwapMax > emaMin and emaMax > vwapMin\n* list withinRange = tickers with close > ema10Day * 0.99 and close < ema10Day * 1.01\n
"""
    # g_query = "Feature: v2\nScenario: test\nGiven stocks from list 360ONE, 3MINDIA, AARTIDRUGS, AARTIIND\nWhen let close = latest in 1 samples of day close\nThen list breaker = tickers with close > 1000\n"
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
    # check.obj["test"]["query_df"].to_csv("query_df.csv", index=False)
    print(check.errors)
    print(check.obj["test"]["tickers"])
    # print(check.obj["test"]["logic_tickers"]["breaker"])
    print("elasped time", time.time() - start)

"""Feature: v2
Scenario: test
Given stocks from index nifty50
* stocks from index niftybank
When let changeEma10 = change in 30 samples of day close ema 10
Then get tickers with changeEma10 > 0.1
When let close = latest in 1 samples of day close
* let ma150 = latest in 1 samples of day close ma 150
* let ma200 = latest in 1 samples of day close ma 200
* let ma50 = latest in 1 samples of day close ma 50
* let rateMa200 = rate in 60 samples of day close ma 200
* let wk52Low = minimum in 52 samples of week close
* let wk52High = maximum in 52 samples of week close
Then let closeMaComparison = close > ma50 and close > ma150 and close > ma200
* let maComparison = ma50 > ma150 and ma150 > ma200
* let closeOhlcComparision = close > 1.25 * wk52Low and close > 0.75 * wk52High
* get tickers with closeMaComparison and maComparison and closeOhlcComparision and rateMa200 > 0
"""

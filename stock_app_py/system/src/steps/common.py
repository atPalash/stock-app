import re

from enum import Enum
from typing import Callable
import numpy

import pandas

from stock_app_py.utility.src.path_helper import get_app_path
from stock_app_py.utility.src.yaml_parser import read_config


class PipeType(Enum):
    OR = 1
    AND = 2
    NOT = 3
    PASS = 4
    COL = 5


class VariablePlaceholder(Enum):
    KEYWORD = "keyword"
    MULTISELECTION = "multiselection"
    SELECTION = "selection"
    NUMBER = "number"
    LIST = "list"


class QueryType(Enum):
    QUERY = "query"  # query to filter stocks
    CHART = "chart"  # query to make to a selected ticker chart
    ANY = "any"


class StepRet:
    def __init__(
        self,
        data=None,
        result_df: pandas.DataFrame = None,
        pipe_tickers: list = [],
        pipe_type: PipeType = PipeType.AND,
        variable_id: str = "",
        err: str = "",
    ) -> None:
        self.data = data
        self.result_df = result_df
        self.pipe_tickers = pipe_tickers
        self.pipe_type = pipe_type
        self.variable_id = variable_id
        self.err = err


class VariableTypes(Enum):
    NAME = "name"
    OPERATOR = "operator"
    SAMPLES = "samples"
    INTERVAL = "interval"
    OHLC = "ohlc"
    INDICATOR = "indicator"
    WINDOW = "window"
    CONDITION = "condition"
    TICKER = "ticker"
    INDEX = "index"


class StepData:
    condition = [">", "<", "!=", "==", ">=", "<="]
    color = ["red", "green", "blue"]
    empty = [""]
    index = list(read_config(get_app_path("index_stock.yaml")).keys())
    stocks = read_config(get_app_path("selected_stocks.yaml"))["stock"]
    interval = list(
        read_config(get_app_path("indicator.yaml"))["indicator"]["data"].keys()
    )
    list = ["<list>"]
    number = ["<number>"]
    ohlc = ["close", "open", "high", "low", "volume"]
    indicator = ["ma", "ema", "atr", "rsi"]
    bbands = ["upperbband", "lowerbband", "middlebband"]
    word = ["<word>"]
    condition = ["<condition>"]  # multiline condition
    operator = [
        "latest",
        "oldest",
        "minimum",
        "maximum",
        "average",
        "rate",
        "change",
        "slope",
    ]
    series = ["<series>"]

    def __init__(
        self,
        logic=Callable,
        variables={},
        step_version="v2",
        placeholders={},
        query_type=QueryType.QUERY,
        meta={},
    ) -> None:
        self.logic = logic
        self.variables = variables
        self.step_version = step_version
        self.placeholders = placeholders
        self.query_type = query_type
        self.meta = meta

    def eval_operator(self, operator, span: int, data: numpy.array):
        if operator in self.operator:
            if operator == "latest":
                return data[-1]
            elif operator == "oldest":
                return data[0]
            elif operator == "minimum":
                return numpy.min(data)
            elif operator == "maximum":
                return numpy.max(data)
            elif operator == "average":
                return round(numpy.mean(data), 2)
            elif operator == "rate":
                return round((data[-1] - data[0]) / span, 2)
            elif operator == "change":
                return round((data[-1] - data[0]) / data[0], 2)
            elif operator == "slope":
                return round(numpy.polyfit(numpy.arange(len(data)), data, 1)[0], 2)
        else:
            raise Exception(f"No matching operator found {operator}")


class GherkinQueryRet:
    def __init__(
        self,
        parent: str,
        type: str,
        step: str,
        errors: str,
        result: StepRet,
        meta: dict = {},
        step_version: str = "v1",
    ) -> None:
        self.parent = parent
        self.type = type
        self.step = step
        self.errors = errors
        self.result = result
        self.meta = meta
        self.step_version = step_version


def make_return(prev_step_result: GherkinQueryRet, curr_step_ret: StepRet) -> StepRet:
    prev_step_tickers = []
    curr_step_tickers = curr_step_ret.pipe_tickers
    pipe_type = curr_step_ret.pipe_type
    try:
        prev_step_tickers = prev_step_result.result.pipe_tickers
    except Exception as e:
        pass
    ret = StepRet(data=curr_step_ret.data, err=curr_step_ret.err, pipe_type=pipe_type)
    ret.pipe_tickers = pipe_ticker_list(curr_step_tickers, prev_step_tickers, pipe_type)
    return ret


def get_matched_step(rule: str, steps: dict) -> dict:
    """Find the step which matches rule from steps.

    Args:
        rule (str): string to match.
        steps (dict): allowed dict of steps e.g steps in given.

    Returns:
        dict: return result as dict which consists of matched func and pipe type.
    """
    result = {"matched": False, "match": None, "func": None, "pipe": PipeType.AND}
    if "remove" in rule:
        result["pipe"] = PipeType.NOT
        rule = rule.replace("remove", "").strip()
    elif "add" in rule:
        result["pipe"] = PipeType.OR
        rule = rule.replace("add", "").strip()

    for pattern, step_data in steps.items():
        match = re.search(pattern, rule)
        if match:
            result["matched"] = True
            result["match"] = match
            result["func"] = step_data.logic
            result["query_type"] = step_data.query_type.value
            result["meta"] = step_data.meta
            break
    return result


def pipe_ticker_list(current_ticker_list, update_ticker_list, pipe_type: PipeType):
    # Update the piped tickers
    pipe_tickers = []
    if pipe_type == PipeType.OR:
        """Combine 2 list of tickers and create a pipe_ticker which includes the tickers
        without repeation

        Returns:
            dict: of tickers and piped_tickers
        """
        pipe_tickers = sorted(list(set(current_ticker_list + update_ticker_list)))
    elif pipe_type == PipeType.AND:
        """Combine 2 list of tickers and create a pipe_ticker which includes the tickers
        which exists in both the list

        Returns:
            dict: of tickers and piped_tickers
        """
        pipe_tickers = sorted(list(set(current_ticker_list) & set(update_ticker_list)))
    elif pipe_type == PipeType.NOT:
        """Combine 2 list of tickers and create a pipe_ticker which includes the tickers
        which doesn't exist in list tickers.

        Returns:
            dict: of tickers and piped_tickers
        """
        pipe_tickers = [
            item for item in current_ticker_list if item not in update_ticker_list
        ]
    elif pipe_type == PipeType.PASS:
        pipe_tickers = pipe_tickers
    return pipe_tickers


def update_df(
    df: pandas.DataFrame, ticker_update_list: list, pipe_type: PipeType
) -> pandas.DataFrame:
    def ticker_add_to_df(ticker_list):
        ticker_to_add = pandas.DataFrame(ticker_list, columns=["ticker"])
        # Set the other columns of the new DataFrame to 0
        for column in df.columns:
            if column not in ticker_to_add.columns:
                ticker_to_add[column] = ""
            # Reorder the new rows columns to match the original DataFrame
        ticker_to_add = ticker_to_add[df.columns]
        ret = pandas.concat([df, ticker_to_add], ignore_index=True)
        ret = ret.sort_values(by="ticker")
        ret = ret.reset_index(drop=True)
        return ret

    if len(df) == 0:
        """Add the update list ticker to df

        Returns:
            pandas.Dataframe: of tickers
        """
        return ticker_add_to_df(ticker_update_list)
    elif pipe_type == PipeType.OR:
        existing_tickers = df["ticker"].to_list()
        ticker_to_add = [
            item for item in ticker_update_list if item not in existing_tickers
        ]
        return ticker_add_to_df(ticker_to_add)
    elif pipe_type == PipeType.AND or pipe_type == PipeType.NOT:
        """Remove the tickers that are not present in df['ticker'] & update list

        Returns:
            pandas.Dataframe: of tickers
        """
        ret = df[df["ticker"].isin(ticker_update_list)]
        ret = ret.reset_index(drop=True)
    elif pipe_type == PipeType.PASS:
        ret = df
    return ret


if __name__ == "__main__":
    ch = StepData.stocks
    print(ch)

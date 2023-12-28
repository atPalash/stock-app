import re

from enum import Enum
from typing import Callable


class PipeType(Enum):
    OR = 1
    AND = 2
    NOT = 3
    PASS = 4


class StepRet:
    def __init__(
        self,
        data,
        pipe_tickers: list = [],
        pipe_type: PipeType = PipeType.AND,
        err: str = "",
    ) -> None:
        self.data = data
        self.pipe_tickers = pipe_tickers
        self.pipe_type = pipe_type
        self.err = err


class StepData:
    condition = [">", "<", "!=", "==", ">=", "<="]
    color = ["red", "green", "blue"]
    empty = [""]
    index = ["all", "nifty50", "nifty100"]
    interval = ["day", "week", "hour"]
    list = ["<list>"]
    number = ["<number>"]
    ohlc = ["close", "open", "high", "low"]

    def __init__(self, logic=Callable, variables={}) -> None:
        self.logic = logic
        self.variables = variables


class GherkinQueryRet:
    def __init__(
        self,
        parent: str,
        type: str,
        step: str,
        errors: str,
        result: StepRet,
        meta: dict = {},
    ) -> None:
        self.parent = parent
        self.type = type
        self.step = step
        self.errors = errors
        self.result = result
        self.meta = meta


def make_return(prev_step_result: GherkinQueryRet, curr_step_ret: StepRet) -> StepRet:
    prev_step_tickers = []
    curr_step_tickers = curr_step_ret.pipe_tickers
    pipe_type = curr_step_ret.pipe_type
    try:
        prev_step_tickers = prev_step_result.result.pipe_tickers
    except Exception as e:
        pass
    ret = StepRet(data=curr_step_ret.data, err=curr_step_ret.err, pipe_type=pipe_type)

    # Update the piped tickers
    if pipe_type == PipeType.OR:
        """Combine 2 list of tickers and create a pipe_ticker which includes the tickers
        without repeation

        Returns:
            dict: of tickers and piped_tickers
        """
        ret.pipe_tickers = sorted(list(set(curr_step_tickers + prev_step_tickers)))
    elif pipe_type == PipeType.AND:
        """Combine 2 list of tickers and create a pipe_ticker which includes the tickers
        which exists in both the list

        Returns:
            dict: of tickers and piped_tickers
        """
        ret.pipe_tickers = sorted(list(set(curr_step_tickers) & set(prev_step_tickers)))
    elif pipe_type == PipeType.NOT:
        """Combine 2 list of tickers and create a pipe_ticker which includes the tickers
        which doesn't exist in list tickers.

        Returns:
            dict: of tickers and piped_tickers
        """
        ret.pipe_tickers = [
            item for item in prev_step_tickers if item not in curr_step_tickers
        ]
    elif pipe_type == PipeType.PASS:
        ret.pipe_tickers = curr_step_ret.pipe_tickers
    return ret


def get_matched_step(rule: str, steps: dict):
    result = {"matched": False, "match": None, "func": None}
    for pattern, step_data in steps.items():
        match = re.search(pattern, rule)
        if match:
            result["matched"] = True
            result["match"] = match
            result["func"] = step_data.logic
            result["variables"] = step_data.variables
            break
    return result

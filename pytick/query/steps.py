import re
from enum import Enum
from typing import Callable
import numpy
import pandas


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
    list = ["<list>"]
    number = ["<number>"]
    ohlc = ["close", "open", "high", "low", "volume"]
    indicator = ["ma", "ema", "atr", "rsi", "vwap", "rvol"]
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
        # "slope",
    ]
    interval = ['day', 'minute5', 'minute1']
    series = ["<series>"]

    def __init__(
        self,
        logic=Callable,
        variables={},
        step_version="v2",
        placeholders={},
        query_type=QueryType.QUERY,
        meta={},
        indexes=[],
        stocks = [],
        intervals = [],
    ) -> None:
        self.logic = logic
        self.variables = variables
        self.step_version = step_version
        self.placeholders = placeholders
        self.query_type = query_type
        self.meta = meta
        self.index = indexes
        self.stocks = stocks
        self.interval = intervals

    def eval_operator(self, operator, span: int, data: numpy.array):
        if operator in self.operator:
            try:
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
                # elif operator == "slope":
                #     return round(numpy.polyfit(numpy.arange(len(data)), data, 1)[0], 2)
            except Exception as e:
                raise Exception(f"Error in operator {operator} {e.args}")
        else:
            raise Exception(f"No matching operator found {operator}")


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


    def given_steps(self):
        return {
            r"^stocks from index (.+)$": StepData(
                # logic=stocks.get_stocks,
                variables={3: ['nifty50']},
                placeholders={3: VariablePlaceholder.MULTISELECTION.value},
                query_type=QueryType.ANY,
                meta={
                    3: {
                        "type": VariableTypes.INDEX.value,
                        "input_type": VariablePlaceholder.MULTISELECTION.value,
                    },
                },
            ),
            r"^stocks from list (.+)$": StepData(
                # logic=stocks.get_stocks,
                variables={3: ['BEL', 'TCS']},
                placeholders={3: VariablePlaceholder.MULTISELECTION.value},
                query_type=QueryType.ANY,
                meta={
                    3: {
                        "type": VariableTypes.TICKER.value,
                        "input_type": VariablePlaceholder.MULTISELECTION.value,
                    },
                },
            ),
        }

    def when_steps(self):
        return {
            #  let ema20 = latest in  5   samples of (day)  close  ema    window
            #  0    1    2  3    4    5     6     7   8     9     10    11
            r"^let (\w+) = (\w+) in (\d+) samples of (\w+) (\w+) (\w+) (\d+)$": StepData(
                # logic=indicator.calculate,
                variables={
                    1: StepData.word,
                    3: StepData.operator,
                    5: StepData.number,
                    8: StepData.interval,
                    9: StepData.ohlc,
                    10: StepData.indicator,
                    11: StepData.number,
                },
                step_version="v2",
                meta={
                    1: {
                        "input_type": VariablePlaceholder.KEYWORD.value,
                    },
                    3: {
                        "input_type": VariablePlaceholder.SELECTION.value,
                    },
                    5: {
                        "input_type": VariablePlaceholder.NUMBER.value,
                    },
                    8: {
                        "input_type": VariablePlaceholder.SELECTION.value,
                    },
                    9: {
                        "input_type": VariablePlaceholder.SELECTION.value,
                    },
                    10: {
                        "input_type": VariablePlaceholder.SELECTION.value,
                    },
                    11: {
                        "input_type": VariablePlaceholder.NUMBER.value,
                    },
                },
            ),
            #  let close = latest in  5   samples of  day  close
            #   0   1    2  3    4    5     6     7    8    9
            r"^let (\w+) = (\w+) in (\d+) samples of (\w+) (\w+)$": StepData(
                # logic=ohlc.calculate,
                variables={
                    1: StepData.word,
                    3: StepData.operator,
                    5: StepData.number,
                    8: StepData.interval,
                    9: StepData.ohlc + ["notification"],
                },
                step_version="v2",
                meta={
                    1: {
                        "input_type": VariablePlaceholder.KEYWORD.value,
                    },
                    3: {
                        "input_type": VariablePlaceholder.SELECTION.value,
                    },
                    5: {
                        "input_type": VariablePlaceholder.NUMBER.value,
                    },
                    8: {
                        "input_type": VariablePlaceholder.SELECTION.value,
                    },
                    9: {
                        "input_type": VariablePlaceholder.SELECTION.value,
                    },
                },
            ),
            #  plot close = 5     samples of  day  close
            #   0   1    2 3     4       5    6     7
            r"^plot (\w+) = (\d+) samples of (\w+) (\w+)$": StepData(
                # logic=ohlc.plot,
                variables={
                    1: StepData.word,
                    3: StepData.number,
                    6: StepData.interval,
                    7: StepData.ohlc,
                },
                step_version="v2",
                query_type=QueryType.CHART,
                meta={
                    1: {"type": VariableTypes.NAME.value},
                    3: {"type": VariableTypes.SAMPLES.value},
                    6: {
                        "type": VariableTypes.INTERVAL.value,
                        "readOnly": True,
                        "listenerId": "onIntervalChange",
                    },
                    7: {"type": VariableTypes.OHLC.value},
                },
            ),
            #   0    1    2   3      4    5    6     7     8     9
            r"^plot (\w+) = (\d+) samples of (\w+) (\w+) (\w+) (\d+)$": StepData(
                # logic=indicator.plot,
                variables={
                    1: StepData.word,
                    3: StepData.number,
                    6: StepData.interval,
                    7: StepData.ohlc,
                    8: StepData.indicator,
                    9: StepData.number,
                },
                meta={
                    1: {"type": VariableTypes.NAME.value},
                    3: {"type": VariableTypes.SAMPLES.value},
                    6: {
                        "type": VariableTypes.INTERVAL.value,
                        "readOnly": True,
                        "listenerId": "onIntervalChange",
                    },
                    7: {"type": VariableTypes.OHLC.value},
                    8: {"type": VariableTypes.INDICATOR.value},
                    9: {"type": VariableTypes.WINDOW.value},
                },
                step_version="v2",
                query_type=QueryType.CHART,
            ),
        }

    def then_steps(self):
        return {
            # list tickers with <logic>, user can ask for multiple list names
            r"^list (\w+) = tickers with (.+)$": StepData(
                # logic=list_stocks.calculate,
                variables={
                    1: StepData.word,
                    5: StepData.condition,
                },
                query_type=QueryType.QUERY,
                meta={
                    1: {
                        "type": VariableTypes.NAME.value,
                        "input_type": VariablePlaceholder.KEYWORD.value,
                    },
                    5: {
                        "type": VariableTypes.CONDITION.value,
                        "input_type": VariablePlaceholder.KEYWORD.value,
                    },
                },
            ),
            r"^let (\w+) = (.+)$": StepData(
                # logic=condition.calculate,
                variables={
                    1: StepData.word,
                    3: StepData.condition,
                },
                query_type=QueryType.QUERY,
                meta={
                    1: {
                        "type": VariableTypes.NAME.value,
                        "input_type": VariablePlaceholder.KEYWORD.value,
                    },
                    3: {
                        "type": VariableTypes.CONDITION.value,
                        "input_type": VariablePlaceholder.KEYWORD.value,
                    },
                },
            ),
            #   0   1    2   3      4     5
            r"^plot (\w+) = signals with (.+)$": StepData(
                # logic=signals.calculate,
                variables={
                    1: StepData.word,
                    5: StepData.condition,
                },
                meta={
                    1: {
                        "type": VariableTypes.NAME.value,
                        "input_type": VariablePlaceholder.KEYWORD.value,
                    },
                    5: {
                        "type": VariableTypes.CONDITION.value,
                        "input_type": VariablePlaceholder.KEYWORD.value,
                    },
                },
                query_type=QueryType.CHART,
            ),
        }




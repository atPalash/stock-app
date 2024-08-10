from stock_app_py.system.src.steps.common import QueryType, StepData, VariableTypes
from stock_app_py.system.src.steps.then import condition
from stock_app_py.system.src.steps.when import (
    backtest,
    eps,
    indicator,
    macd,
    ohlc,
    rs_rating,
)

from typing import Callable
import pandas
import re


def get_result(lookback_window: int, logic: Callable, ticker_df: pandas.DataFrame):
    try:
        result = logic(ticker_df)
        if lookback_window == -1:
            return result
        else:
            # start_index =
            index_conditions = []
            for i in range(
                ticker_df.index.stop - lookback_window, ticker_df.index.stop
            ):
                look_back_df = ticker_df.loc[0:i]
                ret = logic(look_back_df)
                if ret["exception"] is not None:
                    result["exception"] = result["exception"] + ret["exception"]
                timestamp = (
                    ticker_df.loc[i]["Datetime"]
                    if "Datetime" in ticker_df.columns
                    else ticker_df.loc[i]["Date"]
                )
                index_conditions.append(
                    (i, timestamp, ret["condition"], ret.get("signal", 0))
                )
            # result["condition"] = pandas.DataFrame(index_conditions, columns=['index', 'eval'])
            result["condition"] = index_conditions
            return result
    except Exception as e:
        raise


def get_result_double_df(
    lookback_window: int,
    logic: Callable,
    ticker_df1: pandas.DataFrame,
    ticker_df2: pandas.DataFrame,
):
    result = logic(ticker_df1, ticker_df2)
    if lookback_window == -1:
        return result
    else:
        # start_index =
        index_conditions = []
        for i in range(ticker_df1.index.stop - lookback_window, ticker_df1.index.stop):
            look_back_df1 = ticker_df1.loc[0:i]
            look_back_df2 = ticker_df2.loc[0:i]
            ret = logic(look_back_df1, look_back_df2)
            if ret["exception"] is not None:
                result["exception"] = result["exception"] + ret["exception"]
            timestamp = (
                ticker_df1.loc[i]["Datetime"]
                if "Datetime" in ticker_df1.columns
                else ticker_df1.loc[i]["Date"]
            )
            index_conditions.append((i, timestamp, ret["condition"]))
        # result["condition"] = pandas.DataFrame(index_conditions, columns=['index', 'eval'])
        result["condition"] = index_conditions
        return result


def get_steps():
    return {
        #  let ema20 = latest in  5   samples of day  close  ema   <otpional number paramaters>
        #  0    1    2  3    4    5     6     7   8     9     10        11
        r"^let (\w+) = (\w+) in (\d+) samples of (\w+) (\w+) (\w+) (\d+)$": StepData(
            logic=indicator.calculate,
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
        ),
        #  let upbband = latest in  5 samples of day  close  upperbband <otpional number paramaters>
        #  0    1      2  3    4    5     6     7   8     9     10        11
        r"^let (\w+) = (\w+) in (\d+) samples of (\w+) (\w+) (\w+) (\d+(?:,\s?\d+)*)$": StepData(
            logic=indicator.calculate,
            variables={
                1: StepData.word,
                3: StepData.operator,
                5: StepData.number,
                8: StepData.interval,
                9: StepData.ohlc,
                10: StepData.bbands,
                11: StepData.word,
            },
            step_version="v2",
        ),
        #  let close = latest in  5   samples of  day  close
        #   0   1    2  3    4    5     6     7    8    9
        r"^let (\w+) = (\w+) in (\d+) samples of (\w+) (\w+)$": StepData(
            logic=ohlc.calculate,
            variables={
                1: StepData.word,
                3: StepData.operator,
                5: StepData.number,
                8: StepData.interval,
                9: StepData.ohlc,
            },
            step_version="v2",
        ),
        #   0    1    2   3      4    5    6     7     8     9
        r"^plot (\w+) = (\d+) samples of (\w+) (\w+) (\w+) (\d+)$": StepData(
            logic=indicator.plot,
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


def _append(original: list, new: list):
    return original + new

from stock_app_py.system.src.steps.common import StepData
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
        # day close ema 50 > close
        r"^(\w+) (\w+) (\w+) (\d+) ([><=!]+) (\w+)$": StepData(
            logic=indicator.indicator_compare_with_ohlc,
            variables={
                0: StepData.interval,
                1: StepData.ohlc,
                2: ["ema", "ma"],
                3: StepData.number,
                4: StepData.condition,
                5: StepData.ohlc,
            },
        ),
        # day close ema 50 > day close ma 20
        r"^(\w+) (\w+) (\w+) (\d+) ([><=!]+) (\w+) (\w+) (\w+) (\d+)$": StepData(
            logic=indicator.indicator_compare_indicator,
            variables={
                0: StepData.interval,
                1: StepData.ohlc,
                2: ["ema", "ma"],
                3: StepData.number,
                4: StepData.condition,
                5: StepData.interval,
                6: StepData.ohlc,
                7: ["ema", "ma"],
                8: StepData.number,
            },
        ),
        # day close ma 50 in uptrend for 90 days
        r"^(\w+) (\w+) (\w+) (\d+) in (\w+) for (\d+) days$": StepData(
            logic=indicator.indicator_slope_compare_value,
            variables={
                0: StepData.interval,
                1: StepData.ohlc,
                2: ["ema", "ma"],
                3: StepData.number,
                5: ["uptrend", "downtrend"],
                7: StepData.number,
            },
        ),
        # 1.25 of 52 week low < close
        r"^([-+]?\d*\.\d+) of (\d+) (\w+) (\w+) ([><=!]+) (\w+)$": StepData(
            logic=ohlc.ohlc_compare_value,
            variables={
                0: StepData.number,
                2: StepData.number,
                3: StepData.interval,
                4: StepData.ohlc,
                5: StepData.condition,
                6: StepData.ohlc,
            },
        ),
        # day close > high of last 20 ticks
        r"^(\w+) (\w+) ([><=!]+) (\w+) of last (\d+) ticks$": StepData(
            logic=ohlc.ohlc_window_compare,
            variables={
                0: StepData.interval,
                1: StepData.ohlc,
                2: StepData.condition,
                3: StepData.ohlc,
                6: StepData.number,
            },
        ),
        # day close shows macd divergence with fastperiod 13 slowperiod 26 signalperiod 9 window 20 in last 100 ticks
        #    0    1    2     3     4        5    6         7      8      9       10     11  12   13 14  15   16   17
        r"^(\w+) (\w+) shows macd divergence with window (\d+) fastperiod (\d+) slowperiod (\d+) signalperiod (\d+) in last (\d+) ticks$": StepData(
            logic=macd.shows_macd_divergence,
            variables={
                0: StepData.interval,
                1: StepData.ohlc,
                7: StepData.number,
                9: StepData.number,
                11: StepData.number,
                13: StepData.number,
                16: StepData.number,
            },
        ),
        # day close shows macd divergence with window 20 in last 100 ticks
        r"^(\w+) (\w+) shows macd divergence with window (\d+) in last (\d+) ticks$": StepData(
            logic=macd.shows_macd_divergence,
            variables={
                0: StepData.interval,
                1: StepData.ohlc,
                7: StepData.number,
                10: StepData.number,
            },
        ),
        # backtest for last 100 ticks | day close > high of last 20 ticks - default color red
        r"^backtest for last (\d+) ticks \| (.*)$": StepData(
            logic=backtest.backtest,
            variables={
                3: StepData.number,
            },
        ),
        # backtest for last 100 ticks with signal color red | day close > high of last 20 ticks
        r"^backtest for last (\d+) ticks with signal color (\w+) \| (.*)$": StepData(
            logic=backtest.backtest,
            variables={
                3: StepData.number,
                8: StepData.color,
            },
        ),
        # quarterly earnings net growth rate > 20 %
        # quarterly earnings recent growth rate > 20 %
        r"^quarterly earnings (\w+) growth rate ([><=!]+) (\d+) %$": StepData(
            logic=eps.quaterly_eps_growth,
            variables={
                2: ["net", "recent"],
                5: StepData.condition,
                6: StepData.number,
            },
        ),
        # quarterly earnings quarter to quarter growth rate > 20 %
        r"^quarterly earnings quarter to quarter growth rate ([><=!]+) (\d+) %$": StepData(
            logic=eps.quaterly_eps_growth,
            variables={
                7: StepData.condition,
                8: StepData.number,
            },
        ),
        # relative strength in nifty100 > 20
        r"^relative strength in (\w+) ([><=!]+) (\d+)$": StepData(
            logic=rs_rating.rs_rating,
            variables={
                3: StepData.index,
                4: StepData.condition,
                5: StepData.number,
            },
        ),
        # relative strength > 80
        r"^relative strength ([><=!]+) (\d+)$": StepData(
            logic=rs_rating.rs_rating,
            variables={
                2: StepData.condition,
                3: StepData.number,
            },
        ),
        #  let ema20 = latest in  5    day  close  ema   50
        r"^let (\w+) = (\w+) in (\d+) (\w+) (\w+) (\w+) (\d+)$": StepData(
            logic=indicator.calculate,
            variables={
                1: StepData.word,
                3: StepData.operator,
                5: StepData.number,
                6: StepData.interval,
                7: StepData.ohlc,
                8: StepData.indicator,
                9: StepData.number,
            },
            step_version='v2'
        ),
        #  let close = latest in  5    day  close
        r"^let (\w+) = (\w+) in (\d+) (\w+) (\w+)$": StepData(
            logic=ohlc.calculate,
            variables={
                1: StepData.word,
                3: StepData.operator,
                5: StepData.number,
                6: StepData.interval,
                7: StepData.ohlc,
            },
            step_version='v2'
        ),
    }

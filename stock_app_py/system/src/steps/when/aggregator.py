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
        r"^(\w+) (\w+) (\w+)\s+(\d+)\s+([><=!]+)\s+(\w+)$": indicator.indicator_compare_with_ohlc,
        # day close ema 50 > day close ma 20
        r"^(\w+) (\w+) (\w+)\s+(\d+)\s+([><=!]+)\s+(\w+) (\w+)\s+(\w+)\s+(\d+)$": indicator.indicator_compare_indicator,
        # day close ma 50 in uptrend for 90 days
        r"^(\w+) (\w+) (\w+)\s+(\d+) in (\w+) for (\d+) days$": indicator.indicator_slope_compare_value,
        # 1.25 of 52 week low < close
        r"^([-+]?\d*\.\d+) of (\d+) (\w+) (\w+)\s+([><=!]+)\s+(\w+)$": ohlc.ohlc_compare_value,
        # day close > high of last 20 ticks
        r"^(\w+) (\w+)\s+([><=!]+)\s+(\w+) of last (\d+) ticks$": ohlc.ohlc_window_compare,
        # day close shows macd divergence with fastperiod 13 slowperiod 26 signalperiod 9 window 20 in last 100 ticks
        r"^(\w+) (\w+) shows macd divergence with window (\d+) fastperiod (\d+) slowperiod (\d+) signalperiod (\d+) in last (\d+) ticks$": macd.shows_macd_divergence,
        # day close shows macd divergence with window 20 in last 100 ticks
        r"^(\w+) (\w+) shows macd divergence with window (\d+) in last (\d+) ticks$": macd.shows_macd_divergence,
        # backtest for last 100 ticks | day close > high of last 20 ticks - default color red
        r"^backtest for last (\d+) ticks \| (.*)$": backtest.backtest,
        # backtest for last 100 ticks with signal color red | day close > high of last 20 ticks
        r"^backtest for last (\d+) ticks with signal color (\w+) \| (.*)$": backtest.backtest,
        # quarterly earnings net growth rate > 20%
        # quarterly earnings recent growth rate > 20%
        r"^quarterly earnings (\w+) growth rate ([><=!]+) (\d+)%$": eps.quaterly_eps_growth,
        # quarterly earnings quarter to quarter growth rate > 20%
        r"^quarterly earnings quarter to quarter growth rate ([><=!]+) (\d+)%$": eps.quaterly_eps_growth,
        # relative strength in nifty100 > 20
        r"^relative strength in (\w+) ([><=!]+) (\d+)$": rs_rating.rs_rating,
        # relative strength > 80
        r"^relative strength ([><=!]+) (\d+)$": rs_rating.rs_rating,
    }

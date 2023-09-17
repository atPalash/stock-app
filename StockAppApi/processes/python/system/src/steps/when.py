import pandas
import numpy
from scipy.stats import linregress
import re
from typing import Callable

from StockAppApi.base.python.src.yaml_parser import read_config
from StockAppApi.utility.python.bdd.steps import when
import StockAppApi.processes.python.system.src.command_handler as executor


@when
def indicator_compare_with_ohlc(selected_stocks_yaml, indicator_config_yaml, ticker, groups, lookback_window:int=-1) -> dict:
    try:
        command_handler = executor.CommandHandler(
            selected_stocks_yaml, indicator_config_yaml)
        interval, ohlc_source_ind_lsh, ind_lhs, ind_lhs_window, condition, \
            ohlc_rhs = groups
        indicator_query = f'talibquery --ticker {ticker} \
                --interval {interval} --do get --csv 0 \
                --indicator {ind_lhs} --window {ind_lhs_window} --n 1000 \
                --ohlc {ohlc_source_ind_lsh.capitalize()}'
        ticker_df = command_handler.execute(indicator_query, is_rest=False).obj
        def logic(df: pandas.DataFrame):
            condition_string = f'{df[ind_lhs.capitalize()].iloc[-1]} {condition} {df[ohlc_rhs.capitalize()].iloc[-1]}'
            return {
                "ticker": ticker,
                "interval": interval,
                "query": indicator_query,
                "condition": eval(condition_string),
                "exception": None
            }
        return __get_result(lookback_window=lookback_window, logic=logic, ticker_df=ticker_df)
    except Exception as e:
        return {
            "ticker": ticker,
            "exception": e.args
        }


@when
def indicator_compare_indicator(selected_stocks_yaml, indicator_config_yaml, ticker, groups, lookback_window: int = -1):
    try:
        command_handler = executor.CommandHandler(
            selected_stocks_yaml, indicator_config_yaml)
        interval_lhs, ohlc_source_ind_lsh, ind_lhs, ind_lhs_window, condition, \
            interval_rhs, ohlc_source_ind_rsh, ind_rhs, ind_rhs_window = groups

        ind_lhs_query = f'talibquery --ticker {ticker} \
                --interval {interval_lhs} --do get --csv 0 \
                --indicator {ind_lhs} --window {ind_lhs_window} --n 1000 \
                --ohlc {ohlc_source_ind_lsh.capitalize()}'
        ind_rhs_query = f'talibquery --ticker {ticker} \
                --interval {interval_rhs} --do get --csv 0 \
                --indicator {ind_rhs} --window {ind_rhs_window} --n 1000 \
                --ohlc {ohlc_source_ind_rsh.capitalize()}'
        ticker_df_lhs = command_handler.execute(
            ind_lhs_query, is_rest=False).obj[ind_lhs]
        ticker_df_rhs = command_handler.execute(
            ind_rhs_query, is_rest=False).obj[ind_rhs]

        def logic(df_lhs, df_rhs):
            condition_string = f'{df_lhs.iloc[-1]} {condition} {df_rhs.iloc[-1]}'
            return {
                "ticker": ticker,
                "interval": ind_lhs_query,
                "lhs_query": ind_lhs_query,
                "rhs_query": ind_rhs_query,
                "condition": eval(condition_string),
                "exception": None
            }
        return __get_result_double_df(lookback_window=lookback_window, logic=logic, ticker_df1=ticker_df_lhs, ticker_df2=ticker_df_rhs)
    except Exception as e:
        return {
            "ticker": ticker,
            "exception": e.args
        }


@when
def indicator_slope_compare_value(selected_stocks_yaml, indicator_config_yaml, ticker, groups, lookback_window: int = -1):
    try:
        command_handler = executor.CommandHandler(
            selected_stocks_yaml, indicator_config_yaml)
        interval, ohlc_source_ind_lsh, ind_lhs, ind_lhs_window, trend, \
            days_span = groups
        indicator_query = f'talibquery --ticker {ticker} \
                --interval {interval} --do get --csv 0 \
                --indicator {ind_lhs} --window {ind_lhs_window} --n 1000 \
                --ohlc {ohlc_source_ind_lsh.capitalize()}'
        ticker_df = command_handler.execute(
            indicator_query, is_rest=False).obj[ind_lhs]

        def logic(df: pandas.DataFrame):
            df = df.tail(int(days_span))
            slope, _, _, _, _ = linregress(
                numpy.arange(0, df.shape[0], 1), df)
            condition = '>' if trend == 'uptrend' else '<'
            condition_string = f'{slope} {condition} 0'
            return {
                "ticker": ticker,
                "interval": interval,
                "query": indicator_query,
                "condition": eval(condition_string),
                "exception": None
            }
        return __get_result(lookback_window=lookback_window, logic=logic, ticker_df=ticker_df)
    except Exception as e:
        return {
            "ticker": ticker,
            "exception": e.args
        }


@when
def ohlc_compare_value(selected_stocks_yaml, indicator_config_yaml, ticker, groups, lookback_window: int = -1):
    try:
        mulitplier, window, interval, ohlc_lhs, condition, ohlc_rhs = groups
        ticker_ohlc_csv_path = f'{read_config(indicator_config_yaml)["indicator"]["data"][interval]}/{ticker}.csv'
        ticker_df = pandas.read_csv(ticker_ohlc_csv_path)

        def logic(df: pandas.DataFrame):
            # lhs ohlc
            rhs = df[ohlc_rhs.capitalize()].iloc[-1]
            # remove the current
            df = df.drop(df.index[-1])
            lhs = (df[ohlc_lhs.capitalize()].tail(int(window)).min()) * float(mulitplier) if ohlc_lhs == "low" else (df[ohlc_lhs.capitalize()].tail(
                int(window)).max()) * float(mulitplier)
            condition_string = f'{lhs} {condition} {rhs}'
            return {
                "ticker": ticker,
                "interval": interval,
                "query": "ohlc read from csv",
                "condition": eval(condition_string),
                "exception": None
            }

        return __get_result(lookback_window=lookback_window, logic=logic, ticker_df=ticker_df)
    except Exception as e:
        return {
            "ticker": ticker,
            "exception": e.args
        }


@when
def ohlc_window_compare(selected_stocks_yaml, indicator_config_yaml, ticker, groups, lookback_window: int = -1):
    try:
        interval, ohlc_lhs, condition, ohlc_rhs, window = groups
        ticker_ohlc_csv_path = f'{read_config(indicator_config_yaml)["indicator"]["data"][interval]}/{ticker}.csv'
        ticker_df = pandas.read_csv(ticker_ohlc_csv_path)

        def logic(df: pandas.DataFrame):
            # lhs ohlc
            lhs = df[ohlc_lhs.capitalize()].iloc[-1]
            # remove the current
            df = df.drop(df.index[-1])
            rhs = df[ohlc_rhs.capitalize()].tail(int(window)).min() if condition == "<" else df[ohlc_rhs.capitalize()].tail(
                int(window)).max()
            condition_string = f'{lhs} {condition} {rhs}'
            return {
                "ticker": ticker,
                "interval": interval,
                "query": "ohlc_window_compare",
                "condition": eval(condition_string),
                "exception": None
            }

        return __get_result(lookback_window=lookback_window, logic=logic, ticker_df=ticker_df)
    except Exception as e:
        return {
            "ticker": ticker,
            "exception": e.args
        }


@when
def shows_macd_divergence(selected_stocks_yaml, indicator_config_yaml, ticker, groups, lookback_window: int = -1):
    try:
        command_handler = executor.CommandHandler(
            selected_stocks_yaml, indicator_config_yaml)
        if len(groups) == 7:
            interval, ohlc, window, fastperiod, slowperiod, signalperiod, tickcount = groups
        elif len(groups) == 4:
            interval, ohlc, window, tickcount = groups
            fastperiod = 12
            slowperiod = 26
            signalperiod = 9
        else:
            raise ("Valid parameters not found")

        macdhist_query = f'talibquery --ticker {ticker} --interval {interval} --do get \
                    --indicator macdhist --fastperiod {fastperiod} \
                    --slowperiod {slowperiod} --signalperiod {signalperiod} \
                    --n 1000 --latest 0 --window {window} \
                    --ohlc {ohlc.capitalize()}'

        ticker_df = command_handler.execute(
            macdhist_query, is_rest=False).obj

        window = int(window)
        # for i in range(ret.index.min(), ret.index.max() - window + 1, 1):
        def logic(df:pandas.DataFrame):
            roll_window_start_index = df.index.stop - window
            roll_window = df.loc[roll_window_start_index:df.index.stop]
            window_macdhist = roll_window['macdhist']
            window_macdhist_min = window_macdhist.min()
            window_macdhist_max = window_macdhist.max()

            divergence = 0
            # Check if the data has divergence in the samples, ie machist values oscillates
            if window_macdhist_min < 0 and window_macdhist_max > 0:
                window_macdhist_min_index = window_macdhist[window_macdhist ==
                                                            window_macdhist_min].index[0]
                window_macdhist_max_index = window_macdhist[window_macdhist ==
                                                            window_macdhist_max].index[0]

                # Check bullish divergence. The two mins must be on both sides
                # of the zero-cross. Start with finding the first min on left of
                # max.
                if window_macdhist_min_index < window_macdhist_max_index:
                    sub_window = roll_window.loc[window_macdhist_max_index:df.index.stop]
                    sub_window_macdhist = sub_window['macdhist']
                    sub_window_macdhist_min = sub_window_macdhist.min()
                    sub_window_macdhist_max = sub_window_macdhist.max()

                    # Check if we get second min after zero-cross. Second
                    # min on right of max
                    if sub_window_macdhist_min < 0 and sub_window_macdhist_max > 0:
                        sub_window_macdhist_min_index = sub_window_macdhist[
                            sub_window_macdhist == sub_window_macdhist_min].index[0]

                        # check for divergence condition
                        priceA = roll_window[ohlc.capitalize()
                                             ].loc[window_macdhist_min_index]
                        priceC = roll_window[ohlc.capitalize()
                                             ].loc[sub_window_macdhist_min_index]
                        macdhistA = window_macdhist_min
                        macdhistC = sub_window_macdhist_min
                        if priceA > priceC and macdhistA < macdhistC:
                            divergence = 1

                # Check bearish divergence. The two maxs must be on both the
                # sides of the zero-cross. First start with finding the
                # first max is left of min
                if window_macdhist_min_index > window_macdhist_max_index:
                    sub_window = roll_window.loc[window_macdhist_min_index:df.index.stop]
                    sub_window_macdhist = sub_window['macdhist']
                    sub_window_macdhist_min = sub_window_macdhist.min()
                    sub_window_macdhist_max = sub_window_macdhist.max()

                    # Check if we get second max after zero-cross. the 2nd
                    # max is right of min.
                    if sub_window_macdhist_min < 0 and sub_window_macdhist_max > 0:
                        sub_window_macdhist_max_index = sub_window_macdhist[
                            sub_window_macdhist == sub_window_macdhist_max].index[0]

                        # check for divergence condition
                        priceA = roll_window[ohlc.capitalize()
                                             ].loc[window_macdhist_max_index]
                        priceC = roll_window[ohlc.capitalize()
                                             ].loc[sub_window_macdhist_max_index]
                        macdhistA = window_macdhist_max
                        macdhistC = sub_window_macdhist_max
                        if priceA < priceC and macdhistA > macdhistC:
                            divergence = -1

            return {
                "ticker": ticker,
                "interval": interval,
                "condition": divergence != 0,
                "signal": divergence,
                "exception": None
            }
        return __get_result(lookback_window=lookback_window, logic=logic, ticker_df=ticker_df)
    except Exception as e:
        return {
            "ticker": ticker,
            "exception": e.args
        }


@when
def backtest(selected_stocks_yaml, indicator_config_yaml, ticker, groups):
    """Method to call to set backtest criteria. This method is a 2-part step.
    Step 1: set the backtest criteria
    Step 2: set the logic to backtest on 
    The steps are separated by |. 

    e.g. "backtest for last 100 ticks | day close > high of last 20 ticks"
    regex: r'^backtest for last (\d+) ticks \| (.*)$'

    Args:
        selected_stocks_yaml (_type_): selected stock list
        indicator_config_yaml (_type_): indicator configuration
        ticker (_type_): stock to test
        groups (_type_): match groups from user input

    Returns: 
    A dictionary with a key "condition" which contains indexes and value
    of step2 logic.
    """
    try:
        if len(groups) == 3:
            look_back_window, signal_color, signal_condition = groups
        elif len(groups) == 2:
            look_back_window, signal_condition = groups
            signal_color = "red"
        else:
            raise Exception("Backtest query format error")

        matched_step = __call_if_step_matched(signal_condition)
        if matched_step["matched"]:
            ret = matched_step["func"](
                selected_stocks_yaml, indicator_config_yaml, ticker, matched_step["match"].groups(), int(look_back_window))
            return {
                "ticker": ticker,
                "interval": ret["interval"],
                "query": "backtest",
                "condition": ret["condition"],
                "color": signal_color,
                "exception": ret["exception"]
            }
        else:
            raise Exception(
                f'Exception in matching keyword {signal_condition}')

    except Exception as e:
        return {
            "ticker": ticker,
            "exception": e.args
        }


def get_steps():
    return {
        # day close ema 50 > close
        r'^(\w+) (\w+) (\w+)\s+(\d+)\s+([><=!]+)\s+(\w+)$': indicator_compare_with_ohlc,
        # day close ema 50 > day close ma 20
        r'^(\w+) (\w+) (\w+)\s+(\d+)\s+([><=!]+)\s+(\w+) (\w+)\s+(\w+)\s+(\d+)$': indicator_compare_indicator,
        # day close ma 50 in uptrend for 90 days
        r'^(\w+) (\w+) (\w+)\s+(\d+) in (\w+) for (\d+) days$': indicator_slope_compare_value,
        # 1.25 of 52 week low < close
        r'^([-+]?\d*\.\d+) of (\d+) (\w+) (\w+)\s+([><=!]+)\s+(\w+)$': ohlc_compare_value,
        # day close > high of last 20 ticks
        r'^(\w+) (\w+)\s+([><=!]+)\s+(\w+) of last (\d+) ticks$': ohlc_window_compare,
        # day close shows macd divergence with fastperiod 13 slowperiod 26 signalperiod 9 window 20 in last 100 ticks
        r'^(\w+) (\w+) shows macd divergence with window (\d+) fastperiod (\d+) slowperiod (\d+) signalperiod (\d+) in last (\d+) ticks$': shows_macd_divergence,
        # day close shows macd divergence with window 20 in last 100 ticks
        r'^(\w+) (\w+) shows macd divergence with window (\d+) in last (\d+) ticks$': shows_macd_divergence,
        # backtest for last 100 ticks | day close > high of last 20 ticks - default color red
        r'^backtest for last (\d+) ticks \| (.*)$': backtest,
        # backtest for last 100 ticks with signal color red | day close > high of last 20 ticks
        r'^backtest for last (\d+) ticks with signal color (\w+) \| (.*)$': backtest
    }


def __get_result(lookback_window: int, logic: Callable, ticker_df: pandas.DataFrame):
    result = logic(ticker_df)
    if lookback_window == -1:
        return result
    else:
        # start_index =
        index_conditions = []
        for i in range(ticker_df.index.stop - lookback_window, ticker_df.index.stop):
            look_back_df = ticker_df.loc[0:i]
            ret = logic(look_back_df)
            if ret["exception"] is not None:
                result["exception"] = result["exception"] + ret["exception"]
            timestamp = ticker_df.loc[i]['Datetime'] if 'Datetime' in ticker_df.columns else ticker_df.loc[i]['Date']
            index_conditions.append((i, timestamp, ret["condition"], ret.get("signal", 0)))
        # result["condition"] = pandas.DataFrame(index_conditions, columns=['index', 'eval'])
        result["condition"] = index_conditions
        return result


def __get_result_double_df(lookback_window: int, logic: Callable, ticker_df1: pandas.DataFrame, ticker_df2: pandas.DataFrame):
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
            timestamp = ticker_df1.loc[i]['Datetime'] if 'Datetime' in ticker_df1.columns else ticker_df1.loc[i]['Date']
            index_conditions.append((i, timestamp, ret["condition"]))
        # result["condition"] = pandas.DataFrame(index_conditions, columns=['index', 'eval'])
        result["condition"] = index_conditions
        return result


def __call_if_step_matched(rule: str):
    result = {
        'matched': False,
        'match': None,
        'func': None
    }
    for pattern, func in get_steps().items():
        match = re.search(pattern, rule)
        if match:
            result['matched'] = True
            result['match'] = match
            result['func'] = func
            break
    return result


if __name__ == "__main__":
    configFolder = "StockAppApi/configuration/"
    indicator_config_yaml = configFolder + "indicator.yaml"
    selected_stocks_yaml = configFolder + "selected_stocks.yaml"
    ticker = 'SBIN'
    query = "day close > high of last 20 ticks"
    # query = "day close shows macd divergence with window 20 fastperiod 12 slowperiod 26 signalperiod 9 in last 40 ticks"
    matched_step = __call_if_step_matched(query)
    result = matched_step['func'](selected_stocks_yaml, indicator_config_yaml,
                                  ticker, matched_step["match"].groups())
    print(result)

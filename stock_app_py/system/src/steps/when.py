import random
import pandas
import numpy
from scipy.stats import linregress
import re
from typing import Callable
import datetime
from stock_app_py.utility.src import date_helper
from stock_app_py.utility.src.path_helper import get_app_path

from stock_app_py.utility.src.yaml_parser import read_config
from stock_app_py.system.src.rs_rating import RsRating
from stock_app_py.utility.src.steps import when
import stock_app_py.system.src.command_handler as executor


@when
def indicator_compare_with_ohlc(
    selected_stocks_yaml,
    indicator_config_yaml,
    ticker,
    groups,
    lookback_window: int = -1,
) -> dict:
    try:
        command_handler = executor.CommandHandler(
            selected_stocks_yaml, indicator_config_yaml
        )
        (
            interval,
            ohlc_source_ind_lsh,
            ind_lhs,
            ind_lhs_window,
            condition,
            ohlc_rhs,
        ) = groups
        indicator_query = f"talibquery --ticker {ticker} \
                --interval {interval} --do get --csv 0 \
                --indicator {ind_lhs} --window {ind_lhs_window} --n 1000 \
                --ohlc {ohlc_source_ind_lsh.capitalize()}"
        ticker_df = command_handler.execute(indicator_query, is_rest=False).obj

        def logic(df: pandas.DataFrame):
            condition_string = f"{df[ind_lhs].iloc[-1]} {condition} {df[ohlc_rhs.capitalize()].iloc[-1]}"
            return {
                "ticker": ticker,
                "interval": interval,
                "query": indicator_query,
                "condition": eval(condition_string),
                "exception": None,
            }

        return __get_result(
            lookback_window=lookback_window, logic=logic, ticker_df=ticker_df
        )
    except Exception as e:
        return {"ticker": ticker, "exception": e.args}


@when
def indicator_compare_indicator(
    selected_stocks_yaml,
    indicator_config_yaml,
    ticker,
    groups,
    lookback_window: int = -1,
):
    try:
        command_handler = executor.CommandHandler(
            selected_stocks_yaml, indicator_config_yaml
        )
        (
            interval_lhs,
            ohlc_source_ind_lsh,
            ind_lhs,
            ind_lhs_window,
            condition,
            interval_rhs,
            ohlc_source_ind_rsh,
            ind_rhs,
            ind_rhs_window,
        ) = groups

        ind_lhs_query = f"talibquery --ticker {ticker} \
                --interval {interval_lhs} --do get --csv 0 \
                --indicator {ind_lhs} --window {ind_lhs_window} --n 1000 \
                --ohlc {ohlc_source_ind_lsh.capitalize()}"
        ind_rhs_query = f"talibquery --ticker {ticker} \
                --interval {interval_rhs} --do get --csv 0 \
                --indicator {ind_rhs} --window {ind_rhs_window} --n 1000 \
                --ohlc {ohlc_source_ind_rsh.capitalize()}"
        ticker_df_lhs = command_handler.execute(ind_lhs_query, is_rest=False).obj
        ticker_df_rhs = command_handler.execute(ind_rhs_query, is_rest=False).obj

        def logic(df_lhs, df_rhs):
            condition_string = (
                f"{df_lhs.iloc[-1][ind_lhs]} {condition} {df_rhs.iloc[-1][ind_rhs]}"
            )
            return {
                "ticker": ticker,
                "interval": ind_lhs_query,
                "lhs_query": ind_lhs_query,
                "rhs_query": ind_rhs_query,
                "query": f"{ind_lhs_query},{ind_rhs_query}",
                "condition": eval(condition_string),
                "exception": None,
            }

        return __get_result_double_df(
            lookback_window=lookback_window,
            logic=logic,
            ticker_df1=ticker_df_lhs,
            ticker_df2=ticker_df_rhs,
        )
    except Exception as e:
        return {"ticker": ticker, "exception": e.args}


@when
def indicator_slope_compare_value(
    selected_stocks_yaml,
    indicator_config_yaml,
    ticker,
    groups,
    lookback_window: int = -1,
):
    try:
        command_handler = executor.CommandHandler(
            selected_stocks_yaml, indicator_config_yaml
        )
        (
            interval,
            ohlc_source_ind_lsh,
            ind_lhs,
            ind_lhs_window,
            trend,
            days_span,
        ) = groups
        indicator_query = f"talibquery --ticker {ticker} \
                --interval {interval} --do get --csv 0 \
                --indicator {ind_lhs} --window {ind_lhs_window} --n 1000 \
                --ohlc {ohlc_source_ind_lsh.capitalize()}"
        ticker_df = command_handler.execute(indicator_query, is_rest=False).obj

        def logic(df: pandas.DataFrame):
            df = df.tail(int(days_span))
            slope, _, _, _, _ = linregress(numpy.arange(0, df.shape[0], 1), df[ind_lhs])
            condition = ">" if trend == "uptrend" else "<"
            condition_string = f"{slope} {condition} 0"
            return {
                "ticker": ticker,
                "interval": interval,
                "query": indicator_query,
                "condition": eval(condition_string),
                "exception": None,
            }

        return __get_result(
            lookback_window=lookback_window, logic=logic, ticker_df=ticker_df
        )
    except Exception as e:
        return {"ticker": ticker, "exception": e.args}


@when
def ohlc_compare_value(
    selected_stocks_yaml,
    indicator_config_yaml,
    ticker,
    groups,
    lookback_window: int = -1,
):
    try:
        mulitplier, window, interval, ohlc_lhs, condition, ohlc_rhs = groups
        ticker_ohlc_csv_path = f'{read_config(indicator_config_yaml)["indicator"]["data"][interval]}/{ticker}.csv'
        ticker_df = pandas.read_csv(ticker_ohlc_csv_path)

        def logic(df: pandas.DataFrame):
            # lhs ohlc
            rhs = df[ohlc_rhs.capitalize()].iloc[-1]
            # remove the current
            df = df.drop(df.index[-1])
            lhs = (
                (df[ohlc_lhs.capitalize()].tail(int(window)).min()) * float(mulitplier)
                if ohlc_lhs == "low"
                else (df[ohlc_lhs.capitalize()].tail(int(window)).max())
                * float(mulitplier)
            )
            condition_string = f"{lhs} {condition} {rhs}"
            return {
                "ticker": ticker,
                "interval": interval,
                "query": "ohlc read from csv",
                "condition": eval(condition_string),
                "exception": None,
            }

        return __get_result(
            lookback_window=lookback_window, logic=logic, ticker_df=ticker_df
        )
    except Exception as e:
        return {"ticker": ticker, "exception": e.args}


@when
def ohlc_window_compare(
    selected_stocks_yaml,
    indicator_config_yaml,
    ticker,
    groups,
    lookback_window: int = -1,
):
    try:
        interval, ohlc_lhs, condition, ohlc_rhs, window = groups
        ticker_ohlc_csv_path = f'{read_config(indicator_config_yaml)["indicator"]["data"][interval]}/{ticker}.csv'
        ticker_df = pandas.read_csv(ticker_ohlc_csv_path)

        def logic(df: pandas.DataFrame):
            # lhs ohlc
            lhs = df[ohlc_lhs.capitalize()].iloc[-1]
            # remove the current
            df = df.drop(df.index[-1])
            rhs = (
                df[ohlc_rhs.capitalize()].tail(int(window)).min()
                if condition == "<"
                else df[ohlc_rhs.capitalize()].tail(int(window)).max()
            )
            condition_string = f"{lhs} {condition} {rhs}"
            return {
                "ticker": ticker,
                "interval": interval,
                "query": "ohlc_window_compare",
                "condition": eval(condition_string),
                "exception": None,
            }

        return __get_result(
            lookback_window=lookback_window, logic=logic, ticker_df=ticker_df
        )
    except Exception as e:
        return {"ticker": ticker, "exception": e.args}


@when
def shows_macd_divergence(
    selected_stocks_yaml,
    indicator_config_yaml,
    ticker,
    groups,
    lookback_window: int = -1,
):
    try:
        command_handler = executor.CommandHandler(
            selected_stocks_yaml, indicator_config_yaml
        )
        if len(groups) == 7:
            (
                interval,
                ohlc,
                window,
                fastperiod,
                slowperiod,
                signalperiod,
                tickcount,
            ) = groups
        elif len(groups) == 4:
            interval, ohlc, window, tickcount = groups
            fastperiod = 12
            slowperiod = 26
            signalperiod = 9
        else:
            raise ("Valid parameters not found")

        macdhist_query = f"talibquery --ticker {ticker} --interval {interval} --do get \
                    --indicator macdhist --fastperiod {fastperiod} \
                    --slowperiod {slowperiod} --signalperiod {signalperiod} \
                    --n 1000 --latest 0 --window {window} \
                    --ohlc {ohlc.capitalize()}"

        ticker_df = command_handler.execute(macdhist_query, is_rest=False).obj
        window = int(window)

        def logic(df: pandas.DataFrame):
            roll_window_start_index = df.index.stop - window
            roll_window = df.loc[roll_window_start_index : df.index.stop]
            window_macdhist = roll_window["macdhist"]
            window_macdhist_min = window_macdhist.min()
            window_macdhist_max = window_macdhist.max()

            divergence = 0
            # Check if the data has divergence in the samples, ie machist values oscillates
            if window_macdhist_min < 0 and window_macdhist_max > 0:
                window_macdhist_min_index = window_macdhist[
                    window_macdhist == window_macdhist_min
                ].index[0]
                window_macdhist_max_index = window_macdhist[
                    window_macdhist == window_macdhist_max
                ].index[0]

                # Check bullish divergence. The two mins must be on both sides
                # of the zero-cross. Start with finding the first min on left of
                # max.
                if window_macdhist_min_index < window_macdhist_max_index:
                    sub_window = roll_window.loc[
                        window_macdhist_max_index : df.index.stop
                    ]
                    sub_window_macdhist = sub_window["macdhist"]
                    sub_window_macdhist_min = sub_window_macdhist.min()
                    sub_window_macdhist_max = sub_window_macdhist.max()

                    # Check if we get second min after zero-cross. Second
                    # min on right of max
                    if sub_window_macdhist_min < 0 and sub_window_macdhist_max > 0:
                        sub_window_macdhist_min_index = sub_window_macdhist[
                            sub_window_macdhist == sub_window_macdhist_min
                        ].index[0]

                        # check for divergence condition
                        priceA = roll_window[ohlc.capitalize()].loc[
                            window_macdhist_min_index
                        ]
                        priceC = roll_window[ohlc.capitalize()].loc[
                            sub_window_macdhist_min_index
                        ]
                        macdhistA = window_macdhist_min
                        macdhistC = sub_window_macdhist_min
                        if priceA > priceC and macdhistA < macdhistC:
                            divergence = 1

                # Check bearish divergence. The two maxs must be on both the
                # sides of the zero-cross. First start with finding the
                # first max is left of min
                if window_macdhist_min_index > window_macdhist_max_index:
                    sub_window = roll_window.loc[
                        window_macdhist_min_index : df.index.stop
                    ]
                    sub_window_macdhist = sub_window["macdhist"]
                    sub_window_macdhist_min = sub_window_macdhist.min()
                    sub_window_macdhist_max = sub_window_macdhist.max()

                    # Check if we get second max after zero-cross. the 2nd
                    # max is right of min.
                    if sub_window_macdhist_min < 0 and sub_window_macdhist_max > 0:
                        sub_window_macdhist_max_index = sub_window_macdhist[
                            sub_window_macdhist == sub_window_macdhist_max
                        ].index[0]

                        # check for divergence condition
                        priceA = roll_window[ohlc.capitalize()].loc[
                            window_macdhist_max_index
                        ]
                        priceC = roll_window[ohlc.capitalize()].loc[
                            sub_window_macdhist_max_index
                        ]
                        macdhistA = window_macdhist_max
                        macdhistC = sub_window_macdhist_max
                        if priceA < priceC and macdhistA > macdhistC:
                            divergence = -1

            return {
                "ticker": ticker,
                "interval": interval,
                "condition": divergence != 0,
                "signal": divergence,
                "exception": None,
            }

        return __get_result(
            lookback_window=lookback_window, logic=logic, ticker_df=ticker_df
        )
    except Exception as e:
        return {"ticker": ticker, "exception": e.args}


@when
def quaterly_eps_growth(
    selected_stocks_yaml,
    indicator_config_yaml,
    ticker,
    groups,
    lookback_window: int = -1,
):
    """Query eps growth with different type
    * net - slope of eps growth
    * recent - growth compared to last quarter
    * quarter to quarter - growth comparted to same quarter last year

    Args:
        selected_stocks_yaml (str): selected stocks list
        indicator_config_yaml (str): indicator config
        ticker (str): ticker name e.g ABB
        groups (regex groups): read the user input value from this
        lookback_window (int, optional): used for backtest as the window to look back and compute the logic

    Returns:
        dict: dictionary containing the result of the logic
    """
    try:
        condition_type = "quarter to quarter"
        if len(groups) == 3:
            condition_type, condition, threshold = groups
        elif len(groups) == 2:
            condition, threshold = groups
        else:
            raise Exception(f"Gherkin query arguments should be 2 or 3 : {groups}")

        command_handler = executor.CommandHandler(
            selected_stocks_yaml, indicator_config_yaml
        )
        financials_query = f"yahoofinance --ticker {ticker} --do financials"
        financials = command_handler.execute(financials_query, is_rest=False).obj
        ohlc_query = f"yahoofinance --ticker {ticker} --interval week --do ohlc"
        ohlc = command_handler.execute(ohlc_query, is_rest=False).obj

        eps = []
        quarters = []
        for quarter, statement in financials["incomeStatementHistoryQuarterly"].items():
            if "basicEPS" in statement:
                eps.append(statement["basicEPS"])
                quarters.append(quarter)

        def net(date):
            try:
                _, index = date_helper.find_closest_date(date, quarters)
                index = index + 1  # include this index also
                start_date = quarters[0]
                quarter_series = [(x - start_date).days for x in quarters[:index]]
                slope, _ = numpy.polyfit(quarter_series, eps[:index], 1)
                return slope
            except Exception as e:
                raise

        def previous_to_quarter(date):
            try:
                _, index = date_helper.find_closest_date(date, quarters)
                index = index + 1  # include this index also
                selected_eps = eps[:index]
                growth_rates = {quarters[0]: 0}
                for i in range(0, len(selected_eps) - 1):
                    beginning_value = selected_eps[i]
                    ending_value = selected_eps[i + 1]
                    growth_rate = round(
                        (ending_value - beginning_value) / beginning_value, 2
                    )
                    growth_rates[quarters[i + 1]] = growth_rate
                return growth_rates[quarters[-1]]
            except Exception as e:
                raise

        def quarter_to_quarter(date):
            try:
                _, index = date_helper.find_closest_date(date, quarters)
                index = index + 1  # include this index also
                selected_eps = eps[:index]
                selected_quarters = quarters[:index]
                this_quarter = selected_quarters[-1]
                previous_year_quarter = this_quarter - datetime.timedelta(days=365)
                previous_year_quarter, index = date_helper.find_closest_date(
                    previous_year_quarter, quarters
                )

                this_quarter_eps = selected_eps[-1]
                previous_year_quarter_eps = selected_eps[index]
                return round(
                    (this_quarter_eps - previous_year_quarter_eps)
                    / previous_year_quarter_eps,
                    2,
                )
            except Exception as e:
                raise

        condition_funcs = {
            "net": net,
            "recent": previous_to_quarter,
            "quarter to quarter": quarter_to_quarter,
        }

        def logic(df: pandas.DataFrame):
            try:
                df_last_date = datetime.datetime.strptime(
                    df.iloc[-1]["Date"], "%Y-%m-%d"
                )
                query_quarter, _ = date_helper.find_closest_date(df_last_date, quarters)
                rate = condition_funcs[condition_type](df_last_date)
                condition_string = f"{rate} {condition} {float(threshold) / 100}"
                return {
                    "ticker": ticker,
                    "query": "quaterly_eps_growth",
                    "interval": "week",
                    "quarter": query_quarter,
                    "condition": eval(condition_string),
                    "exception": None,
                }
            except Exception as e:
                raise

        return __get_result(
            lookback_window=lookback_window, logic=logic, ticker_df=ohlc
        )
    except Exception as e:
        return {"ticker": ticker, "exception": e.args}


@when
def rs_rating(
    selected_stocks_yaml,
    indicator_config_yaml,
    ticker,
    groups,
    lookback_window: int = -1,
):
    """The Relative Strength Rating is the result of calculating
    a stock's percentage price change over the last 12 months. A 40% weight is
    assigned to the latest three-month period; the remaining three quarters each
    receive 20% weight. All stocks are arranged in order of greatest price percentage
    change and assigned a percentile rank from 99 (highest) to 1 (lowest).

    Args:
        selected_stocks_yaml (_type_): _description_
        indicator_config_yaml (_type_): _description_
        ticker (_type_): _description_
        groups (_type_): _description_
        lookback_window (int, optional): _description_. Defaults to -1.

    Returns:
        _type_: _description_
    """
    query_type = "all"
    if len(groups) == 3:
        index, condition, threshold = groups
        query_type = "index"
    elif len(groups) == 2:
        condition, threshold = groups
    else:
        raise Exception(f"Gherkin query arguments should be 2 or 3 : {groups}")

    def percentile_in_all(ticker: str, price_change_df: pandas.DataFrame = None):
        if query_type != "all":
            raise Exception(f"Expected an all here")
        price_change_df.loc[:, "percentile_rank"] = round(
            price_change_df["price_change"].rank(pct=True) * 100, 2
        )
        return price_change_df[price_change_df["ticker"] == ticker][
            "percentile_rank"
        ].iat[0]

    def percentile_in_index(ticker: str, price_change_df: pandas.DataFrame = None):
        if query_type == "all":
            raise Exception(f"Expected an index here")

        index_tickers = command_handler.execute(
            "nsestocklist --do get", is_rest=False
        ).obj[index]
        index_rs_rating = price_change_df[price_change_df["ticker"].isin(index_tickers)]
        index_rs_rating.loc[:, "percentile_rank"] = round(
            index_rs_rating["price_change"].rank(pct=True) * 100, 2
        )
        return index_rs_rating[index_rs_rating["ticker"] == ticker][
            "percentile_rank"
        ].iat[0]

    condition_funcs = {"all": percentile_in_all, "index": percentile_in_index}

    def logic(ticker: str, price_change_df: pandas.DataFrame = None):
        try:
            rs_rating = condition_funcs[query_type](ticker, price_change_df)
            condition_string = f"{rs_rating} {condition} {threshold}"
            return {
                "ticker": ticker,
                "query": "rs_rating",
                "interval": "month",
                "condition": eval(condition_string),
                "value": rs_rating,
                "exception": None,
            }
        except Exception as e:
            raise

    if lookback_window < 0:
        command_handler = executor.CommandHandler(
            selected_stocks_yaml, indicator_config_yaml
        )
        price_change_df = command_handler.execute(
            f"rsrating --ticker {ticker} --do get", is_rest=False
        ).obj

        return logic(ticker=ticker, price_change_df=price_change_df)
    else:
        rs_rating = RsRating(
            indicator_config_file=indicator_config_yaml,
            selected_stocks_config_file=selected_stocks_yaml,
            parameter={},
            command_handler=None,
            name="",
        )

        def do_backtest(lookback_window: int, logic: Callable, tickers_df_map: dict):
            result = {
                "ticker": ticker,
                "query": "rs_rating",
                "interval": "month",
                "value": 0,
                "exception": None,
            }
            try:
                index_conditions = []
                ticker_df = tickers_df_map[ticker]
                ticker_df_index_stop = ticker_df.index.stop
                for i in range(
                    ticker_df_index_stop - lookback_window, ticker_df_index_stop
                ):
                    lookback_df_map = {}
                    for key, val in tickers_df_map.items():
                        # Since the comparision is between a stock wrt to other stock price
                        # the dates need to aligned, since here index is used, the aligned
                        # index refers to the corresponding i ref in the comparison stock. If the
                        # comparison stock doesn't have data for i ref ignore the stock.
                        aligned_index_stop = (val.index.stop - ticker_df_index_stop) + i
                        if aligned_index_stop >= 0:
                            lookback_df_map[key] = val.loc[0:aligned_index_stop]

                    price_change_df = rs_rating.get_price_change(
                        tickers_df_map=lookback_df_map
                    ).obj

                    ret = logic(ticker, price_change_df)
                    if ret["exception"] is not None:
                        result["exception"] = result["exception"] + ret["exception"]
                    timestamp = (
                        ticker_df.loc[i]["Datetime"]
                        if "Datetime" in ticker_df.columns
                        else ticker_df.loc[i]["Date"]
                    )
                    index_conditions.append(
                        (i, timestamp, ret["condition"], ret.get("value", 0))
                    )
                # result["condition"] = pandas.DataFrame(index_conditions, columns=['index', 'eval'])
                result["condition"] = index_conditions
                return result
            except Exception as e:
                raise

        tickers_df_map = {}
        for ticker_i in read_config(selected_stocks_yaml)["stock"]:
            ticker_ohlc_csv_path = f'{read_config(indicator_config_yaml)["indicator"]["data"]["month"]}/{ticker_i}.csv'
            ticker_df = pandas.read_csv(ticker_ohlc_csv_path)
            tickers_df_map[ticker_i] = ticker_df
        return do_backtest(
            lookback_window=lookback_window, logic=logic, tickers_df_map=tickers_df_map
        )


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
    colors = [
        "red",
        "blue",
        "green",
        "yellow",
        "orange",
        "purple",
        "brown",
        "pink",
        "gray",
    ]
    try:
        if len(groups) == 3:
            look_back_window, signal_color, signal_condition = groups
        elif len(groups) == 2:
            look_back_window, signal_condition = groups
            signal_color = random.choice(colors)
        else:
            raise Exception("Backtest query format error")

        matched_step = __call_if_step_matched(signal_condition)
        if matched_step["matched"]:
            ret = matched_step["func"](
                selected_stocks_yaml,
                indicator_config_yaml,
                ticker,
                matched_step["match"].groups(),
                int(look_back_window),
            )
            return {
                "ticker": ticker,
                "interval": ret["interval"],
                "query": f"backtest_{ret['query']}",
                "condition": ret["condition"],
                "color": signal_color,
                "exception": ret["exception"],
            }
        else:
            raise Exception(f"Exception in matching keyword {signal_condition}")

    except Exception as e:
        return {"ticker": ticker, "exception": e.args}


def __get_result(lookback_window: int, logic: Callable, ticker_df: pandas.DataFrame):
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


def __get_result_double_df(
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


def __call_if_step_matched(rule: str):
    result = {"matched": False, "match": None, "func": None}
    for pattern, func in get_steps().items():
        match = re.search(pattern, rule)
        if match:
            result["matched"] = True
            result["match"] = match
            result["func"] = func
            break
    return result


def get_steps():
    return {
        # day close ema 50 > close
        r"^(\w+) (\w+) (\w+)\s+(\d+)\s+([><=!]+)\s+(\w+)$": indicator_compare_with_ohlc,
        # day close ema 50 > day close ma 20
        r"^(\w+) (\w+) (\w+)\s+(\d+)\s+([><=!]+)\s+(\w+) (\w+)\s+(\w+)\s+(\d+)$": indicator_compare_indicator,
        # day close ma 50 in uptrend for 90 days
        r"^(\w+) (\w+) (\w+)\s+(\d+) in (\w+) for (\d+) days$": indicator_slope_compare_value,
        # 1.25 of 52 week low < close
        r"^([-+]?\d*\.\d+) of (\d+) (\w+) (\w+)\s+([><=!]+)\s+(\w+)$": ohlc_compare_value,
        # day close > high of last 20 ticks
        r"^(\w+) (\w+)\s+([><=!]+)\s+(\w+) of last (\d+) ticks$": ohlc_window_compare,
        # day close shows macd divergence with fastperiod 13 slowperiod 26 signalperiod 9 window 20 in last 100 ticks
        r"^(\w+) (\w+) shows macd divergence with window (\d+) fastperiod (\d+) slowperiod (\d+) signalperiod (\d+) in last (\d+) ticks$": shows_macd_divergence,
        # day close shows macd divergence with window 20 in last 100 ticks
        r"^(\w+) (\w+) shows macd divergence with window (\d+) in last (\d+) ticks$": shows_macd_divergence,
        # backtest for last 100 ticks | day close > high of last 20 ticks - default color red
        r"^backtest for last (\d+) ticks \| (.*)$": backtest,
        # backtest for last 100 ticks with signal color red | day close > high of last 20 ticks
        r"^backtest for last (\d+) ticks with signal color (\w+) \| (.*)$": backtest,
        # quarterly earnings net growth rate > 20%
        # quarterly earnings recent growth rate > 20%
        r"^quarterly earnings (\w+) growth rate ([><=!]+) (\d+)%$": quaterly_eps_growth,
        # quarterly earnings quarter to quarter growth rate > 20%
        r"^quarterly earnings quarter to quarter growth rate ([><=!]+) (\d+)%$": quaterly_eps_growth,
        # relative strength in nifty100 > 20
        r"^relative strength in (\w+) ([><=!]+) (\d+)$": rs_rating,
        # relative strength > 80
        r"^relative strength ([><=!]+) (\d+)$": rs_rating,
    }


if __name__ == "__main__":
    indicator_config_yaml = get_app_path('indicator.yaml')
    selected_stocks_yaml = get_app_path('selected_stocks.yaml')
    ticker = "LT"
    # query = "relative strength > 20"
    query = "backtest for last 10 ticks | relative strength > 20"
    # query = "backtest for last 100 ticks | day close ma 200 in uptrend for 60 days"
    matched_step = __call_if_step_matched(query)
    result = matched_step["func"](
        selected_stocks_yaml,
        indicator_config_yaml,
        ticker,
        matched_step["match"].groups(),
    )
    print(result)

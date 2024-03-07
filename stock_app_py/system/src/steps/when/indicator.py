from stock_app_py.system.src.steps.common import StepData
from stock_app_py.utility.src.steps import when
import stock_app_py.system.src.command_handler as executor
from stock_app_py.system.src.steps.when import aggregator

import pandas
from scipy.stats import linregress
import numpy


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

        return aggregator.get_result(
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

        return aggregator.get_result_double_df(
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

        return aggregator.get_result(
            lookback_window=lookback_window, logic=logic, ticker_df=ticker_df
        )
    except Exception as e:
        return {"ticker": ticker, "exception": e.args}


@when
def calculate(
    selected_stocks_yaml,
    indicator_config_yaml,
    ticker,
    groups,
    query_df=None,
    ticker_df=None,
    lookback_window: int = -1,
) -> dict:
    command_handler = executor.CommandHandler(
        selected_stocks_yaml, indicator_config_yaml
    )
    variable_id, operator, query_span, interval, ohlc_source, indicator, window = groups
    query_span = int(query_span)
    indicator_query = f"talibquery --ticker {ticker} \
                --interval {interval} --do get --csv 0 \
                --indicator {indicator} --window {window} --n 1000 \
                --ohlc {ohlc_source.capitalize()}"
    temp_df = command_handler.execute(indicator_query, is_rest=False, ticker_df=ticker_df).obj
    temp_df = (
        temp_df.tail(query_span)
        .reset_index(drop=True)
        .rename(columns={temp_df.columns[-1]: variable_id})
    )
    return {
        "ticker": ticker,
        "interval": interval,
        "query": indicator_query,
        "condition": True,
        f"{variable_id}_df": temp_df,
        "variable_id": variable_id,
        "operator": operator,
        "span": query_span,
        "exception": None,
    }

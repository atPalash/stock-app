import pandas
import numpy
from scipy.stats import linregress

from StockAppApi.base.python.src.yaml_parser import read_config
from StockAppApi.utility.python.bdd.steps import when
import StockAppApi.processes.python.system.src.command_handler as executor

@when
def indicator_compare_with_ohlc(selected_stocks_yaml, indicator_config_yaml, ticker, groups) -> dict:
    try:
        command_handler = executor.CommandHandler(
            selected_stocks_yaml, indicator_config_yaml)
        interval, ohlc_source_ind_lsh, ind_lhs, ind_lhs_window, condition, \
            ohlc_rhs = groups
        indicator_query = f'talibquery --ticker {ticker} \
                --interval {interval} --do get --csv 0 \
                --indicator {ind_lhs} --window {ind_lhs_window} --n 1000 \
                --ohlc {ohlc_source_ind_lsh.capitalize()}'
        df = command_handler.execute(indicator_query, is_rest=False).obj
        df.columns = df.columns.str.lower()
        condition_string = f'{df[ind_lhs].iloc[-1]} {condition} {df[ohlc_rhs].iloc[-1]}'
        return {
            "ticker": ticker,
            "query": indicator_query,
            "condition": eval(condition_string),
            "exception": None
        }
    except Exception as e:
        return {
            "ticker": ticker,
            "exception": e.args
        }


@when
def indicator_compare_indicator(selected_stocks_yaml, indicator_config_yaml, ticker, groups):
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
        df_lhs = command_handler.execute(
            ind_lhs_query, is_rest=False).obj[ind_lhs]
        df_rhs = command_handler.execute(
            ind_rhs_query, is_rest=False).obj[ind_rhs]
        condition_string = f'{df_lhs.iloc[-1]} {condition} {df_rhs.iloc[-1]}'
        return {
            "ticker": ticker,
            "lhs_query": ind_lhs_query,
            "rhs_query": ind_rhs_query,
            "condition": eval(condition_string),
            "exception": None
        }
    except Exception as e:
        return {
            "ticker": ticker,
            "exception": e.args
        }

@when
def indicator_slope_compare_value(selected_stocks_yaml, indicator_config_yaml, ticker, groups):
    try:
        command_handler = executor.CommandHandler(
            selected_stocks_yaml, indicator_config_yaml)
        interval, ohlc_source_ind_lsh, ind_lhs, ind_lhs_window, trend, \
            days_span = groups
        indicator_query = f'talibquery --ticker {ticker} \
                --interval {interval} --do get --csv 0 \
                --indicator {ind_lhs} --window {ind_lhs_window} --n 1000 \
                --ohlc {ohlc_source_ind_lsh.capitalize()}'
        df = command_handler.execute(
            indicator_query, is_rest=False).obj[ind_lhs]
        df = df.tail(int(days_span))
        slope, _, _, _, _ = linregress(
            numpy.arange(0, df.shape[0], 1), df)
        condition = '>' if trend == 'uptrend' else '<'
        condition_string = f'{slope} {condition} 0'
        return {
            "ticker": ticker,
            "query": indicator_query,
            "condition": eval(condition_string),
            "exception": None
        }
    except Exception as e:
        return {
            "ticker": ticker,
            "exception": e.args
        }

@when
def ohlc_compare_value(selected_stocks_yaml, indicator_config_yaml, ticker, groups):
    try:
        mulitplier, window, interval, ohlc_lhs, condition, ohlc_rhs = groups
        ticker_ohlc_csv_path = f'{read_config(indicator_config_yaml)["indicator"]["data"][interval]}/{ticker}.csv'
        df = pandas.read_csv(ticker_ohlc_csv_path)

        # lhs ohlc
        lhs = (df[ohlc_lhs.capitalize()].tail(
            int(window)).min()) * float(mulitplier)
        condition_string = f'{lhs} {condition} {df[ohlc_rhs.capitalize()].iloc[-1]}'
        return {
            "ticker": ticker,
            "query": "ohlc read from csv",
            "condition": eval(condition_string),
            "exception": None
        }
    except Exception as e:
        return {
            "ticker": ticker,
            "exception": e.args
        }

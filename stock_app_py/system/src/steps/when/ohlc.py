from stock_app_py.utility.src.steps import when
from stock_app_py.system.src.steps.when import aggregator
from stock_app_py.utility.src.yaml_parser import read_config

import pandas


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

        return aggregator.get_result(
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

        return aggregator.get_result(
            lookback_window=lookback_window, logic=logic, ticker_df=ticker_df
        )
    except Exception as e:
        return {"ticker": ticker, "exception": e.args}

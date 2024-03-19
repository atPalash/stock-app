from stock_app_py.utility.src.steps import when
from stock_app_py.system.src.steps.when import aggregator, ohlc
import stock_app_py.system.src.command_handler as executor
from stock_app_py.system.src.rs_rating import RsRating
from stock_app_py.utility.src.yaml_parser import read_config

import pandas
from typing import Callable


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
            return {
                "ticker": ticker,
                "query": "rs_rating",
                "interval": "month",
                "condition": False,
                "value": -1,
                "exception": e.args,
            }

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
def __calculate_growth_rate(
    selected_stocks_yaml,
    indicator_config_yaml,
    ticker,
    groups,
    ticker_df,
    lookback_window: int = -1,
) -> dict:
    variable_id, _, query_span, interval, ohlc_source, indicator, window = groups
    variable_id = "growth"
    query_span = int(query_span)
    command_handler = executor.CommandHandler(
        selected_stocks_yaml, indicator_config_yaml
    )
    indicator_query = f"talibquery --ticker {ticker} \
                --interval {interval} --do get --csv 0 \
                --indicator {indicator} --window {window} --n {query_span * 2} \
                --ohlc {ohlc_source.capitalize()}"
    temp_df = command_handler.execute(
        indicator_query, is_rest=False, ticker_df=ticker_df
    ).obj
    temp_df = temp_df.rename(columns={temp_df.columns[-1]: variable_id}).tail(
        query_span
    )
    ref_val = temp_df[variable_id].iloc[0]
    temp_df[variable_id] = round((temp_df[variable_id] - ref_val) / ref_val, 2)

    return {
        "ticker": ticker,
        "interval": interval,
        "query": "rs-rating-1-part",
        "condition": True,
        f"{variable_id}_df": temp_df,
        "variable_id": variable_id,
        "operator": "latest",
        "span": query_span,
        "exception": None,
    }


def __calculate_rs_rating(groups, query_df):
    """Get the pandas dataframe which has growth rate calculated for all the selected
    ticker. The column name is growth and then we will create the relative strength
    of the ticker in this function.

    Args:
        groups (_type_): user defined key, column name of growth
        df (_type_): dataframe with growth rate value

    Returns:
        dict: df and other meta data
    """
    # Calculate the percentile ranks for the growth rates
    rs_key, growth_key = groups
    query_df[rs_key] = query_df[growth_key].rank(pct=True)
    return {
        "query": "rs-rating-2-part",
        "condition": True,
        f"{rs_key}_df": query_df,
        "variable_id": rs_key,
        "operator": "latest",
        "exception": None,
    }


@when
def calculate(
    selected_stocks_yaml=None,
    indicator_config_yaml=None,
    ticker=None,
    groups=None,
    query_df: pandas.DataFrame = None,
    ticker_df: pandas.DataFrame = None,
    lookback_window: int = -1,
) -> dict:
    """This is a step function call
    1. It calls growth to assign growth rate of each stock which is called for
    each ticker by the multi-process thread.
    2. It will then accept a dataframe which has growth rate define and calculate
    the relative strength

    Args:
        selected_stocks_yaml (_type_): required to call with step 1
        indicator_config_yaml (_type_): required to call with step 1
        ticker (_type_): name of ticker
        groups (_type_): define groups step 2. has growth rate defined df.
        lookback_window (int, optional): backtest flag. Defaults to -1.

    Returns:
        dict: dict of result
    """
    if groups != None and len(groups) == 7:
        return __calculate_growth_rate(
            selected_stocks_yaml=selected_stocks_yaml,
            indicator_config_yaml=indicator_config_yaml,
            ticker=ticker,
            groups=groups,
            ticker_df=ticker_df,
        )
    elif not query_df.empty:
        return __calculate_rs_rating(groups, query_df)
    else:
        raise Exception("rs_rating exception")

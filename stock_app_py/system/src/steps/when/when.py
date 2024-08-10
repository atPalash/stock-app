import logging
import pandas
from stock_app_py.system.src.steps.when import rs_rating
from stock_app_py.utility.src.path_helper import get_app_path
from stock_app_py.system.src.steps.when import aggregator
from stock_app_py.system.src.steps import common

import multiprocessing


# Function to handle worker execution with error capture
def worker_function(func, *args):
    try:
        result = func(*args)
        return result, None
    except Exception as e:
        return None, str(e)


def __execute_subprocess(matched_step, args):
    multi_results = []
    errors = []

    with multiprocessing.Pool() as pool:
        try:
            # Prepare arguments for starmap
            starmap_args = [(matched_step["func"], *arg) for arg in args]
            results = pool.starmap(worker_function, starmap_args)

            for result, error in results:
                if error:
                    errors.append(error)
                else:
                    multi_results.append(result)
        except Exception as e:
            logging.error(f"General error in parallel execution: {e}")
            errors.append(f"{e}")
    if errors:
        logging.error(f"Errors during parallel execution: {', '.join(errors)}")
    return multi_results


def __execute_step_v1(
    matched_step: dict,
    prev_step_result: common.GherkinQueryRet,
    pipe_type: common.PipeType,
    selected_stocks_config_file: str,
    indicator_config_file: str,
):
    errors = ""
    pipe_tickers = []
    valid_results = []
    args = [
        (
            selected_stocks_config_file,
            indicator_config_file,
            ticker,
            matched_step["match"].groups(),
        )
        for ticker in prev_step_result.result.pipe_tickers
    ]
    multi_results = __execute_subprocess(matched_step, args)
    for result in multi_results:
        if result["exception"] is None:
            satisfies = False
            if isinstance(result["condition"], bool):
                satisfies = result["condition"]
            if isinstance(result["condition"], list):
                satisfies = any(result["condition"])
            if satisfies:
                valid_results.append(result)
                pipe_tickers.append(result["ticker"])
        else:
            errors += f'{result["ticker"]} -> {result["exception"]} \n'
    valid_results.sort(key=lambda stock: stock["ticker"])

    curr_step_ret = common.StepRet(
        data=valid_results,
        pipe_tickers=pipe_tickers,
        pipe_type=pipe_type,
        err=errors,
    )

    return common.make_return(
        prev_step_result=prev_step_result, curr_step_ret=curr_step_ret
    )


def __execute_step_v2(
    matched_step: dict,
    selected_stocks_config_file: str,
    indicator_config_file: str,
    query_df: pandas.DataFrame,
    tickers_df_dict: dict,
    backtest: bool = False,
):
    args = [
        (
            selected_stocks_config_file,
            indicator_config_file,
            ticker,
            matched_step["match"].groups(),
            query_df,
            tickers_df_dict[ticker],
        )
        for ticker in query_df["ticker"].tolist()
    ]

    multi_results = __execute_subprocess(matched_step, args)
    variable_id = multi_results[0]["variable_id"]
    if matched_step["query_type"] in ["chart"]:
        try:
            # This path is when the query asks for series of calculations. The calculation length are always the same.
            # Here, add the calculations as columns. e.g. dataframe. For chart/backtest we will have onlu 1 row
            # | ticker  | series                |
            # | ABB     | <pandas dataframe>    |
            # The first dataframe is with OHLC data, for the next indicator the indicator data is added as a column.
            if "series" not in query_df.columns:
                query_df["series"] = (
                    None  # We will send a series of data can be indicator data
                )

            for res in multi_results:
                series_df = query_df.at[
                    query_df[query_df["ticker"] == res["ticker"]].index[0], "series"
                ]
                if series_df is None:
                    series_df = res[f"{variable_id}_df"]
                else:
                    series_df[variable_id] = res[f"{variable_id}_df"][variable_id]
                query_df.at[
                    query_df[query_df["ticker"] == res["ticker"]].index[0], "series"
                ] = series_df
            return query_df
        except Exception as e:
            query_df.loc[query_df["ticker"] == res["ticker"], "error"] = (
                query_df.loc[query_df["ticker"] == res["ticker"], "error"]
                + f" when.calculate:{e.args}"
            )
    elif matched_step["query_type"] in ["query"]:
        step_data = common.StepData(logic=None, variables=None, step_version="v2")

        query_df.loc[:, variable_id] = 0.0
        for res in multi_results:
            try:
                operated_value = step_data.eval_operator(
                    res["operator"],
                    res["span"],
                    res[f"{variable_id}_df"][f"{variable_id}"].to_numpy(),
                )
                query_df.loc[query_df["ticker"] == res["ticker"], f"{variable_id}"] = (
                    operated_value
                )
                temp_error = query_df.loc[query_df["ticker"] == res["ticker"], "error"]
                query_df.loc[query_df["ticker"] == res["ticker"], "error"] = (
                    "" if res["exception"] == None else res["exception"] + temp_error
                )
            except Exception as e:
                query_df.loc[query_df["ticker"] == res["ticker"], "error"] = (
                    query_df.loc[query_df["ticker"] == res["ticker"], "error"]
                    + f" when.calculate:{e.args}"
                )
        if matched_step["func"] == rs_rating.calculate:
            rs_id = matched_step["match"].groups()[0]
            groups = (rs_id, variable_id)
            query_df = matched_step["func"](groups=groups, query_df=query_df)[
                f"{rs_id}_df"
            ]
    else:
        raise Exception("No valid query type found ", matched_step)
    query_df = query_df.round(2)
    return query_df


def execute(
    matched_step: dict,
    prev_step_result: common.GherkinQueryRet,
    pipe_type: common.PipeType,
    selected_stocks_config_file: str,
    indicator_config_file: str,
    step_version: str = "v1",
    query_df: pandas.DataFrame = None,
    tickers_df_dict: dict = None,
) -> common.StepRet:
    if step_version == "v1":
        return __execute_step_v1(
            matched_step=matched_step,
            prev_step_result=prev_step_result,
            pipe_type=pipe_type,
            selected_stocks_config_file=selected_stocks_config_file,
            indicator_config_file=indicator_config_file,
        )
    elif step_version == "v2":
        return __execute_step_v2(
            matched_step=matched_step,
            selected_stocks_config_file=selected_stocks_config_file,
            indicator_config_file=indicator_config_file,
            query_df=query_df,
            tickers_df_dict=tickers_df_dict,
        )
    else:
        raise Exception(f"Invalid step version {step_version}")


if __name__ == "__main__":
    indicator_config_yaml = get_app_path("indicator.yaml")
    selected_stocks_yaml = get_app_path("selected_stocks.yaml")
    ticker = "LT"
    query = "let atr14 = latest in 1 samples of day close atr 14"
    # query = "relative strength > 20"
    # query = "backtest for last 10 ticks | relative strength > 20"
    # query = "backtest for last 100 ticks | day close ma 200 in uptrend for 60 days"
    matched_step = common.get_matched_step(query, aggregator.get_steps())
    result = matched_step["func"](
        selected_stocks_yaml,
        indicator_config_yaml,
        ticker,
        matched_step["match"].groups(),
    )
    print(result)

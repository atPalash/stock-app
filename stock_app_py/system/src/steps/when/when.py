import pandas
from stock_app_py.utility.src.path_helper import get_app_path
from stock_app_py.system.src.steps.when import aggregator
from stock_app_py.system.src.steps import common

import multiprocessing


def __execute_subprocess(matched_step, args):
    multi_results = []
    with multiprocessing.Pool() as pool:
        try:
            multi_results = pool.starmap(matched_step["func"], args)
        except Exception as e:
            errors += f"{e.args}"
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
    backtest: bool = False,
):
    args = [
        (
            selected_stocks_config_file,
            indicator_config_file,
            ticker,
            matched_step["match"].groups(),
        )
        for ticker in query_df["ticker"].tolist()
    ]

    multi_results = __execute_subprocess(matched_step, args)
    if backtest:
        # TODO
        return query_df
    else:
        step_data = common.StepData(logic=None, variables=None, step_version="v2")
        query_df[multi_results[0]["variable_id"]] = 0.0
        for res in multi_results:
            try:
                operated_value = step_data.eval_operator(
                    res["operator"],
                    res["span"],
                    res[f'{res["variable_id"]}_df'][f'{res["variable_id"]}'].to_numpy(),
                )
                query_df.loc[
                    query_df["ticker"] == res["ticker"], f'{res["variable_id"]}'
                ] = operated_value
                temp_error = query_df.loc[query_df["ticker"] == res["ticker"], "error"]
                query_df.loc[query_df["ticker"] == res["ticker"], "error"] = (
                    "" if res["exception"] == None else res["exception"] + temp_error
                )
            except Exception as e:
                query_df.loc[query_df["ticker"] == res["ticker"], "error"] = (
                    query_df.loc[query_df["ticker"] == res["ticker"], "error"]
                    + f"when.calculate:{e.args}"
                )

    return query_df


def execute(
    matched_step: dict,
    prev_step_result: common.GherkinQueryRet,
    pipe_type: common.PipeType,
    selected_stocks_config_file: str,
    indicator_config_file: str,
    step_version: str = "v1",
    query_df: pandas.DataFrame = None,
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
        )
    else:
        raise Exception(f"Invalid step version {step_version}")


if __name__ == "__main__":
    indicator_config_yaml = get_app_path("indicator.yaml")
    selected_stocks_yaml = get_app_path("selected_stocks.yaml")
    ticker = "LT"
    query = "let ema10 = latest in 5 day close ema 10"
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

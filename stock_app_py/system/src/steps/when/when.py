from stock_app_py.utility.src.path_helper import get_app_path
from stock_app_py.system.src.steps.when import aggregator
from stock_app_py.system.src.steps import common

import multiprocessing


def execute(
    matched_step: dict,
    prev_step_result: common.GherkinQueryRet,
    pipe_type: common.PipeType,
    selected_stocks_config_file: str,
    indicator_config_file: str,
) -> common.StepRet:
    errors = ""
    pipe_tickers = []
    valid_results = []

    args = []
    for ticker in prev_step_result.result.pipe_tickers:
        args.append(
            (
                selected_stocks_config_file,
                indicator_config_file,
                ticker,
                matched_step["match"].groups(),
            )
        )

    multi_results = None
    with multiprocessing.Pool() as pool:
        try:
            multi_results = pool.starmap(matched_step["func"], args)
        except Exception as e:
            errors += f"{e.args}"

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


if __name__ == "__main__":
    indicator_config_yaml = get_app_path("indicator.yaml")
    selected_stocks_yaml = get_app_path("selected_stocks.yaml")
    ticker = "LT"
    # query = "relative strength > 20"
    query = "backtest for last 10 ticks | relative strength > 20"
    # query = "backtest for last 100 ticks | day close ma 200 in uptrend for 60 days"
    matched_step = common.get_matched_step(query, aggregator.get_steps())
    result = matched_step["func"](
        selected_stocks_yaml,
        indicator_config_yaml,
        ticker,
        matched_step["match"].groups(),
    )
    print(result)

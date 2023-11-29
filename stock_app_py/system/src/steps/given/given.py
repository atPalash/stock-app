from stock_app_py.utility.src.path_helper import get_app_path
from stock_app_py.system.src.steps import common
from stock_app_py.system.src.steps.given import aggregator
from stock_app_py.system.src.steps.common import StepRet, GherkinQueryRet, PipeType


def execute(
    matched_step: dict,
    prev_step_result: GherkinQueryRet,
    pipe_type: PipeType,
    selected_stocks_config_file: str,
    indicator_config_file: str,
) -> StepRet:
    func_ret = matched_step["func"](
        selected_stocks_config_file,
        indicator_config_file,
        matched_step["match"].groups(),
    )

    curr_step_ret = common.StepRet(
        data=func_ret,
        pipe_tickers=func_ret,
        pipe_type=pipe_type,
        err="",
    )

    return common.make_return(
        prev_step_result=prev_step_result, curr_step_ret=curr_step_ret
    )


if __name__ == "__main__":
    indicator_config_yaml = get_app_path("indicator.yaml")
    selected_stocks_yaml = get_app_path("selected_stocks.yaml")

    query = f"remove stocks under surveillance"
    # query = f"all stocks"
    # query = "day close > high of last 20 ticks"
    matched_step = common.get_matched_step(query, aggregator.get_steps())
    result = execute(
        matched_step, {}, PipeType.OR, selected_stocks_yaml, indicator_config_yaml
    )
    print(result.pipe_tickers)

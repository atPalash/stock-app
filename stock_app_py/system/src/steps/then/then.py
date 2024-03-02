import pandas
from stock_app_py.system.src.steps import common


def __execute_step_v1(
    matched_step: dict,
    all_step_result: list,
    pipe_type: common.PipeType,
):
    func_ret = matched_step["func"](all_step_result)
    curr_step_ret = common.StepRet(
        data=func_ret.get("signals", None),
        pipe_tickers=func_ret["tickers"],
        pipe_type=pipe_type,
        err="",
    )

    return common.make_return(
        prev_step_result=all_step_result[-1], curr_step_ret=curr_step_ret
    )


def __execute_step_v2(matched_step: dict, query_df: pandas.DataFrame):
    query_df = matched_step["func"](matched_step['match'].groups()[0], query_df)
    return query_df

def execute(
    matched_step: dict,
    all_step_result: list,
    pipe_type: common.PipeType,
    step_version: str = "v1",
    query_df: pandas.DataFrame = None,
) -> common.StepRet:
    if step_version == "v1":
        return __execute_step_v1(
            matched_step=matched_step,
            all_step_result=all_step_result,
            pipe_type=pipe_type,
        )
    elif step_version == "v2":
        return __execute_step_v2(
            matched_step=matched_step,
            query_df=query_df,
        )
    else:
        raise Exception(f"Invalid step version {step_version}")

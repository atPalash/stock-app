from stock_app_py.system.src.steps import common


def execute(
    matched_step: dict,
    all_step_result: list,
    pipe_type: common.PipeType,
) -> common.StepRet:
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

from stock_app_py.utility.src.steps import then
from stock_app_py.system.src.steps import common


@then
def get_list(all_steps: list) -> dict:
    return {"tickers": all_steps[-1].result.pipe_tickers}

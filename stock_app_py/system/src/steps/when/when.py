from stock_app_py.utility.src.path_helper import get_app_path
from stock_app_py.system.src.steps.when import aggregator
from stock_app_py.system.src.steps import common


def get():
    pass


if __name__ == "__main__":
    indicator_config_yaml = get_app_path("indicator.yaml")
    selected_stocks_yaml = get_app_path("selected_stocks.yaml")
    ticker = "LT"
    # query = "relative strength > 20"
    query = "backtest for last 10 ticks | relative strength > 20"
    # query = "backtest for last 100 ticks | day close ma 200 in uptrend for 60 days"
    matched_step = common.call_if_step_matched(query, aggregator.get_steps())
    result = matched_step["func"](
        selected_stocks_yaml,
        indicator_config_yaml,
        ticker,
        matched_step["match"].groups(),
    )
    print(result)

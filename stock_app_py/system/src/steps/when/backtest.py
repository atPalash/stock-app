import random
from stock_app_py.utility.src.steps import when
from stock_app_py.system.src.steps import common
from stock_app_py.system.src.steps.when import aggregator


@when
def backtest(selected_stocks_yaml, indicator_config_yaml, ticker, groups):
    """Method to call to set backtest criteria. This method is a 2-part step.
    Step 1: set the backtest criteria
    Step 2: set the logic to backtest on
    The steps are separated by |.

    e.g. "backtest for last 100 ticks | day close > high of last 20 ticks"
    regex: r'^backtest for last (\d+) ticks \| (.*)$'

    Args:
        selected_stocks_yaml (_type_): selected stock list
        indicator_config_yaml (_type_): indicator configuration
        ticker (_type_): stock to test
        groups (_type_): match groups from user input

    Returns:
    A dictionary with a key "condition" which contains indexes and value
    of step2 logic.
    """
    colors = [
        "red",
        "blue",
        "green",
        "yellow",
        "orange",
        "purple",
        "brown",
        "pink",
        "gray",
    ]
    try:
        if len(groups) == 3:
            look_back_window, signal_color, signal_condition = groups
        elif len(groups) == 2:
            look_back_window, signal_condition = groups
            signal_color = random.choice(colors)
        else:
            raise Exception("Backtest query format error")

        matched_step = common.call_if_step_matched(
            signal_condition, aggregator.get_steps()
        )
        if matched_step["matched"]:
            ret = matched_step["func"](
                selected_stocks_yaml,
                indicator_config_yaml,
                ticker,
                matched_step["match"].groups(),
                int(look_back_window),
            )
            return {
                "ticker": ticker,
                "interval": ret["interval"],
                "query": f"backtest_{ret['query']}",
                "condition": ret["condition"],
                "color": signal_color,
                "exception": ret["exception"],
            }
        else:
            raise Exception(f"Exception in matching keyword {signal_condition}")

    except Exception as e:
        return {"ticker": ticker, "exception": e.args}

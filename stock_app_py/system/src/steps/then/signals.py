from stock_app_py.utility.src.steps import then
from stock_app_py.system.src.steps import common


@then
def list_stock_signals(all_steps: list) -> dict:
    """
    After generating signals from the when step, the condition of each ticker
    is filled with index and a boolean value signifying when the condition matches
    Here go through all the tickers and select those which satisfy the condition.

    Args:
        all_steps (list): all previous steps, will filter signals in each step.

    Returns:
        ret: {
            tickers: {
                ticker:[(index, condition)...]
            }
        }
    """
    try:
        ret = []
        tickers_with_signal = {}
        for step in all_steps:
            if step.type == "When " or step.parent == "when":
                for stp in step.result.data:
                    if any(
                        isinstance(item, tuple) and item[1] for item in stp["condition"]
                    ):
                        temp = {
                            "signal": stp["condition"],
                            "color": stp["color"],
                            "interval": stp["interval"],
                            "step": step.step,
                        }
                        if stp["ticker"] not in tickers_with_signal:
                            tickers_with_signal[stp["ticker"]] = [temp]
                        else:
                            tickers_with_signal[stp["ticker"]].append(temp)
        return {"tickers": list(tickers_with_signal), "signals": tickers_with_signal}
    except Exception as e:
        return {"exception": e.args}

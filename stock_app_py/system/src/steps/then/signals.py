from stock_app_py.utility.src.steps import then


@then
def list_stock_signals(groups, steps):
    """TODO
    After generating signals from the when step, the condition of each ticker
    is filled with index and a boolean value signifying when the condition matches
    Here go through all the tickers and select those which satisfy the condition.

    Args:
        groups (_type_): matched groups, is empty for this function
        steps (_type_): previous steps

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
        for step in steps:
            if step["type"] == "When " or step["parent"] == "when":
                for stp in step["result"]:
                    if any(
                        isinstance(item, tuple) and item[1] for item in stp["condition"]
                    ):
                        temp = {
                            "signal": stp["condition"],
                            "color": stp["color"],
                            "interval": stp["interval"],
                            "step": step["step"],
                        }
                        if stp["ticker"] not in tickers_with_signal:
                            tickers_with_signal[stp["ticker"]] = [temp]
                        else:
                            tickers_with_signal[stp["ticker"]].append(temp)
        return {"tickers": list(tickers_with_signal), "signals": tickers_with_signal}
    except Exception as e:
        return {"exception": e.args}

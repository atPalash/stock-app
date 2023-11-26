from stock_app_py.utility.src.steps import then


@then
def get_list(groups, steps):
    try:
        selector = groups[0]
        ret = []
        when_step_tickers = []
        for step in steps:
            if step["type"] == "When " or step["parent"] == "when":
                step_tickers = []
                for stp in step["result"]:
                    step_tickers.append(stp["ticker"])
                when_step_tickers.append(step_tickers)

        if selector == "all":
            ret = list(set.intersection(*map(set, when_step_tickers)))
        elif selector == "any":
            ret = list(set.union(*map(set, when_step_tickers)))
        else:
            raise Exception("Not valid selection")
        ret.sort()
        return {"selection": selector, "tickers": ret}
    except Exception as e:
        return {"selection": selector, "exception": e.args}

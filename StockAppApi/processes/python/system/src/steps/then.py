from StockAppApi.utility.python.bdd.steps import then

@then
def get_list(selector, steps):
    try:
        ret = []
        for step in steps:
            if step['type'] == "When " or step["parent"] == "when":
                if len(ret) == 0:
                    ret = step['result']
                else:
                    if selector == 'all':
                        ret = list(set(ret) & set(step['result']))
                    elif selector == 'any':
                        ret = list(set(ret + step['result']))
                    else:
                        raise Exception("Not valid selection")

        return {
            "selection": selector,
            "tickers": ret
        }
    except Exception as e:
        return {
            "selection": selector,
            "exception": e.args
        }

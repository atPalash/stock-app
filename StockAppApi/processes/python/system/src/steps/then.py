from StockAppApi.utility.python.bdd.steps import then

@then
def get_list(groups, steps):
    try:
        selector = groups[0]
        ret = []
        when_step_tickers = []
        for step in steps:
            if step['type'] == "When " or step["parent"] == "when":
                step_tickers = []
                for stp in step['result']:
                    step_tickers.append(stp['ticker'])
                when_step_tickers.append(step_tickers)
        
        if selector == 'all':
            ret = list(set.intersection(*map(set, when_step_tickers)))
        elif selector == 'any':
            ret = list(set.union(*map(set, when_step_tickers)))
        else:
            raise Exception("Not valid selection")
        ret.sort()
        return {
            "selection": selector,
            "tickers": ret
        }
    except Exception as e:
        return {
            "selection": selector,
            "exception": e.args
        }

@then
def color_tickers(selector, steps):
    try:
        return {
            "selection": selector,
            "tickers": []
        }
    except Exception as e:
        return {
            "selection": selector,
            "exception": e.args
        }

@then
def list_stock_signals(groups, steps):
    """ TODO
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
            if step['type'] == "When " or step["parent"] == "when":
                for stp in step['result']:
                    if any(isinstance(item, tuple) and item[1] for item in stp["condition"]):
                        temp = {
                                'signal': stp['condition'],
                                'color': stp['color'] ,
                                'interval': stp['interval'],
                                'step': step['step']
                            }
                        if(stp['ticker'] not in tickers_with_signal):
                            tickers_with_signal[stp['ticker']] = [temp]     
                        else:
                            tickers_with_signal[stp['ticker']].append(temp)
        return {
            "tickers": list(tickers_with_signal),
            "signals": tickers_with_signal
        }
    except Exception as e:
        return {
            "exception": e.args
        }
        
def get_steps():
    return {
        r'^get list of (\w+) match$': get_list,
        r'^get list of stocks with signals$': list_stock_signals,
    }

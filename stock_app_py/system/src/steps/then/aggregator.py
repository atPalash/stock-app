from stock_app_py.system.src.steps.then import color, list_stocks, signals


def get_steps():
    return {
        r"^get list$": list_stocks.get_list,
        r"^get list of stocks with signals$": signals.list_stock_signals,
    }

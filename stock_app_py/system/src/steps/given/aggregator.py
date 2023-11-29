from stock_app_py.system.src.steps.given import stocks


def get_steps():
    return {
        # r'^(\w+)\s+(\d+)\s+stocks$': get_stocks_in_index,
        r"^(\w+)\s+stocks$": stocks.get_index_stocks,
        r"^stocks (\w+(?:,*\s*\w*)*)$": stocks.get_stocks,
        r"^remove\s+stocks\s+(\w+(?:,*\s*\w*)*)$": stocks.get_stocks
        # r'^indexes (\w+(?:,*\s*\w*)*)$': get_stocks
    }

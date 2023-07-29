
from StockAppApi.utility.python.bdd.steps import given

@given
def get_selected_stocks(allTickers, groups):
    try:
        # TODO logic to select selected stocks
        return {
            # TODO set tickers based on selected index
            "tickers": allTickers,
            "exception": None
        }
    except Exception as e:
        return {
            "tickers": None,
            "exception": e.args
        }

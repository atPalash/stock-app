import stock_app_py.system.src.steps.common as comm
from stock_app_py.system.src.steps.common import StepData
from stock_app_py.system.src.steps.then import color, list_stocks, signals


def get_steps():
    return {
        r"^get list$": StepData(
            logic=list_stocks.get_list,
            variables={-1: StepData.empty},
        ),
        r"^get list of stocks with signals$": StepData(
            logic=signals.list_stock_signals,
            variables={-1: StepData.empty},
        ),
        # get tickers with <logic>
        r"^get tickers with ([^.?!]*[+\-*><!=/%][^.?!]*)$": StepData(
            logic=list_stocks.calculate,
            variables={3: StepData.word},
        ),
    }

if __name__ == "__main__":
    query = "get tickers with ema10 * ema50 - ema30 <= ema20 / ma50 - ema10"
    # query = "get list of stocks with signals"
    res = comm.get_matched_step(query, get_steps())
    print(res['match'].groups())

# ([^.?!]*[+\-*></%][^.?!]*)

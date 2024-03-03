import stock_app_py.system.src.steps.common as comm
from stock_app_py.system.src.steps.common import StepData
from stock_app_py.system.src.steps.then import color, list_stocks, signals, condition


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
        r"^get tickers with (.+)$": StepData(
            logic=list_stocks.calculate,
            variables={3: StepData.word},
        ),

        r"^let (\w+) = (.+)$": StepData(
            logic=condition.calculate,
            variables={
                1: StepData.word,
                3: StepData.word,
            },
        ),
    }

if __name__ == "__main__":
    query = "let close_ma150 = close > ma150"
    query = "get tickers with close_ma50 & close_ma150 & close_ma200 & ma50_ma150 & ma50_ma200 & ma150_ma200 & uptrend200 & close_52wklow & close_52wkhigh"
    # query = "get list of stocks with signals"
    res = comm.get_matched_step(query, get_steps())
    print(res['match'].groups())

# ([^.?!]*[+\-*></%][^.?!]*)
        # #  let ma150 = <logic>
        # r"^let (\w+) = ([^.?!]*[+\-*><!=/%][^.?!]*)$": StepData(
        #     logic=condition.calculate,
        #     variables={
        #         1: StepData.word,
        #         3: StepData.word,
        #     },
        # ),

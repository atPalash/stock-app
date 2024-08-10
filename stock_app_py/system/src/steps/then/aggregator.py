import stock_app_py.system.src.steps.common as comm
from stock_app_py.system.src.steps.common import QueryType, StepData, VariableTypes
from stock_app_py.system.src.steps.then import color, condition, list_stocks, signals


def get_steps():
    return {
        # list tickers with <logic>, user can ask for multiple list names
        r"^list (\w+) = tickers with (.+)$": StepData(
            logic=list_stocks.calculate,
            variables={
                1: StepData.word,
                5: StepData.condition,
            },
            query_type=QueryType.QUERY,
            meta={
                1: {"type": VariableTypes.NAME.value},
                5: {"type": VariableTypes.CONDITION.value},
            },
        ),
        r"^let (\w+) = (.+)$": StepData(
            logic=condition.calculate,
            variables={
                1: StepData.word,
                3: StepData.condition,
            },
            query_type=QueryType.QUERY,
            meta={
                1: {"type": VariableTypes.NAME.value},
                3: {"type": VariableTypes.CONDITION.value},
            },
        ),
        #   0   1    2   3      4     5
        r"^plot (\w+) = signals with (.+)$": StepData(
            logic=signals.calculate,
            variables={
                1: StepData.word,
                5: StepData.condition,
            },
            meta={
                1: {"type": VariableTypes.NAME.value},
                5: {"type": VariableTypes.CONDITION.value},
            },
            query_type=QueryType.CHART,
        ),
    }


if __name__ == "__main__":
    # query = "let close_ma150 = close > ma150"
    # query = "get tickers with close_ma50 & close_ma150 & close_ma200 & ma50_ma150 & ma50_ma200 & ma150_ma200 & uptrend200 & close_52wklow & close_52wkhigh"
    # query = "get list of stocks with signals"
    query = "get tickers with abs(ema5 - ema5last) / 5 > 0.01 and abs(ema10 - ema10last) / 5 > 0.01"
    res = comm.get_matched_step(query, get_steps())
    print(res["match"].groups())

# ([^.?!]*[+\-*></%][^.?!]*)
# #  let ma150 = <logic>
# r"^let (\w+) = ([^.?!]*[+\-*><!=/%][^.?!]*)$": StepData(
#     logic=condition.calculate,
#     variables={
#         1: StepData.word,
#         3: StepData.word,
#     },
# ),

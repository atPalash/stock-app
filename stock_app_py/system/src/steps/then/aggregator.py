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
    }

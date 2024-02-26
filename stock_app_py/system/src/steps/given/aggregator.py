from stock_app_py.system.src.steps.given import stocks
from stock_app_py.system.src.steps.common import StepData


def get_steps():
    return {
        # r'^(\w+) (\d+) stocks$': get_stocks_in_index,
        r"^(\w+) stocks$": StepData(
            logic=stocks.get_index_stocks, variables={0: StepData.index}
        ),
        r"^stocks (\w+(?:,*\s*\w*)*)$": StepData(
            logic=stocks.get_stocks, variables={1: StepData.list}
        ),
        r"^stocks (\w+(?:,*\s*\w*)*)$": StepData(
            logic=stocks.get_stocks, variables={2: StepData.list}
        ),
    }

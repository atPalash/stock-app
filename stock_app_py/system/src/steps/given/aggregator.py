from stock_app_py.system.src.steps.given import stocks
from stock_app_py.system.src.steps.common import (
    QueryType,
    StepData,
    VariablePlaceholder,
    VariableTypes,
)


def get_steps():
    return {
        r"^stocks from index (.+)$": StepData(
            logic=stocks.get_stocks,
            variables={3: StepData.index},
            placeholders={3: VariablePlaceholder.MULTISELECTION.value},
            query_type=QueryType.ANY,
            meta={
                3: {"type": VariableTypes.INDEX.value},
            },
        ),
        r"^stocks from list (.+)$": StepData(
            logic=stocks.get_stocks,
            variables={3: StepData.stocks},
            placeholders={3: VariablePlaceholder.MULTISELECTION.value},
            query_type=QueryType.ANY,
            meta={
                3: {"type": VariableTypes.TICKER.value},
            },
        ),
    }

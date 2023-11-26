import stock_app_py.system.src.command_handler as executor
from stock_app_py.system.src.steps.given import aggregator
from stock_app_py.utility.src.steps import given


@given
def ignore_stocks(selected_stocks_yaml, indicator_config_yaml, groups):
    if groups[0] == "under surveillance":
        return __get_surveillance_stocks(selected_stocks_yaml, indicator_config_yaml)
    else:
        return aggregator.extract_stock_list(groups[0])


def __get_surveillance_stocks(
    selected_stocks_yaml,
    indicator_config_yaml,
):
    try:
        command_handler = executor.CommandHandler(
            selected_stocks_yaml, indicator_config_yaml
        )
        surveillance_stocks = command_handler.execute(
            "nsestocklist --do surveillance_stocks", is_rest=False
        ).obj
        return {"tickers": surveillance_stocks, "exception": None}
    except Exception as e:
        return {"tickers": None, "exception": e.args}

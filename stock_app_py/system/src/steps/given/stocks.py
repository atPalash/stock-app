import stock_app_py.system.src.command_handler as executor
from stock_app_py.system.src.steps.given import aggregator
from stock_app_py.utility.src.steps import given


@given
def get_index_stocks(selected_stocks_yaml, indicator_config_yaml, groups):
    """Get a list of stocks based on criteria.

    Args:
        selected_stocks_yaml (_type_): _description_
        indicator_config_yaml (_type_): _description_
        ticker (_type_): _description_
        groups (_type_): _description_

    Returns:
        _type_: _description_
    """
    try:
        index = groups[0]
        command_handler = executor.CommandHandler(
            selected_stocks_yaml, indicator_config_yaml
        )
        ret = command_handler.execute("nsestocklist --do get", is_rest=False).obj

        if index == "all":
            all_tickers = []
            for index, tickers in ret.items():
                for ticker in tickers:
                    if ticker not in all_tickers:
                        all_tickers.append(ticker)
            all_tickers.sort()
            return {"tickers": all_tickers, "exception": None}

        return {"tickers": ret[index], "exception": None}
    except Exception as e:
        return {"tickers": None, "exception": e.args}


def get_stocks(selected_stocks_yaml, indicator_config_yaml, groups):
    return aggregator.extract_stock_list(groups[0])

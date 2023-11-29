import stock_app_py.system.src.command_handler as executor
from stock_app_py.system.src.steps.given import aggregator
from stock_app_py.utility.src.steps import given
from stock_app_py.system.src.steps import common


@given
def get_index_stocks(
    selected_stocks_yaml: str, indicator_config_yaml: str, groups: tuple
) -> list:
    """Get a list of stocks based on criteria.

    Args:
        selected_stocks_yaml (str): selected stocks
        indicator_config_yaml (str): indicator config
        groups (tuple): ticker symbol

    Note: This method is assumed to be first method to be called to set the selection
    of stocks. For this reason by default the pipe_tickers are set here as the
    selected tickers. Also, pipe type is OR so that the return contains the selected
    stocks.

    Returns:
        list: list of tickers
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
            return all_tickers
        return ret[index]
    except Exception as e:
        raise


@given
def get_stocks(
    selected_stocks_yaml: str, indicator_config_yaml: str, groups: tuple
) -> list:
    """Get a list of stocks based on stocks separated by comma or based on some criteria
    e.g. stocks under surveillance.

    Args:
        selected_stocks_yaml (str): selected stocks
        indicator_config_yaml (str): indicator config
        groups (tuple): ticker symbol

    Note: This method is assumed to be first method to be called to set the selection
    of stocks. For this reason by default the pipe_tickers are set here as the
    selected tickers. Also, pipe type is OR so that the return contains the selected
    stocks.

    Returns:
        list: list of tickers
    """
    text_in = groups[0]
    if text_in == "under surveillance":
        return __get_surveillance_stocks(selected_stocks_yaml, indicator_config_yaml)
    elif "," in text_in:
        return __extract_stock_list(text_in)
    elif text_in != "":
        return [text_in]
    else:
        raise Exception(
            f"{get_stocks.__name__} doesn't support the query with {text_in}"
        )


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
        return surveillance_stocks
    except Exception as e:
        raise


def __extract_stock_list(stock_list: str):
    try:
        ticker_str = stock_list.replace(" ", "")
        return ticker_str.split(",") if "," in ticker_str else [ticker_str]
    except Exception as e:
        raise

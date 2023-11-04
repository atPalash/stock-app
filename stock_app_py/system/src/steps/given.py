import re
from stock_app_py.utility.src.path_helper import get_app_path
from stock_app_py.utility.src.steps import given
from stock_app_py.system.base.system import System
import stock_app_py.system.src.command_handler as executor


# TODO deprecate
@given
def get_stocks_in_index(selected_stocks_yaml, indicator_config_yaml, groups):
    """Get a list of stocks based on criteria

    Args:
        selected_stocks_yaml (_type_): _description_
        indicator_config_yaml (_type_): _description_
        ticker (_type_): _description_
        groups (_type_): _description_

    Returns:
        _type_: _description_
    """
    system = System(indicator_config_yaml, selected_stocks_yaml, {}, None)
    all_tickers = system.get_list_of_tickers("stock") + system.get_list_of_tickers(
        "index"
    )
    try:
        # TODO logic to select selected stocks
        return {
            # TODO set tickers based on selected index
            "tickers": all_tickers,
            "exception": None,
        }
    except Exception as e:
        return {"tickers": None, "exception": e.args}


@given
def get_index_stocks(selected_stocks_yaml, indicator_config_yaml, groups):
    """Get a list of stocks based on criteria

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
    ticker_str = groups[0].replace(" ", "")
    return {
        "tickers": ticker_str.split(",") if "," in ticker_str else [ticker_str],
        "exception": None,
    }


def get_steps():
    return {
        # r'^(\w+)\s+(\d+)\s+stocks$': get_stocks_in_index,
        r"^(\w+)\s+stocks$": get_index_stocks,
        r"^stocks (\w+(?:,*\s*\w*)*)$": get_stocks,
        # r'^indexes (\w+(?:,*\s*\w*)*)$': get_stocks
    }


def __call_if_step_matched(rule: str):
    result = {"matched": False, "match": None, "func": None}
    for pattern, func in get_steps().items():
        match = re.search(pattern, rule)
        if match:
            result["matched"] = True
            result["match"] = match
            result["func"] = func
            break
    return result


if __name__ == "__main__":
    indicator_config_yaml = get_app_path('indicator.yaml')
    selected_stocks_yaml = get_app_path('selected_stocks.yaml')

    query = f"stocks BAJAJ-AUTO"
    # query = f'all stocks'
    # query = "day close > high of last 20 ticks"
    matched_step = __call_if_step_matched(query)
    result = matched_step["func"](
        selected_stocks_yaml, indicator_config_yaml, matched_step["match"].groups()
    )
    print(result)
    # import re

    # text = "fruits apple, banana, orange"
    # pattern = r"fruits (\w+(?:,*\s*\w*)*)"

    # match = re.search(pattern, text)
    # if match:
    #     extracted_string = match.group(1)
    #     print(extracted_string)
    # else:
    #     print("No match found.")

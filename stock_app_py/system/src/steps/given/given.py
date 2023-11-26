from stock_app_py.utility.src.path_helper import get_app_path
from stock_app_py.system.src.steps import common
from stock_app_py.system.src.steps.given import aggregator


if __name__ == "__main__":
    indicator_config_yaml = get_app_path("indicator.yaml")
    selected_stocks_yaml = get_app_path("selected_stocks.yaml")

    query = f"ignore stocks under surveillance"
    # query = f'all stocks'
    # query = "day close > high of last 20 ticks"
    matched_step = common.call_if_step_matched(query, aggregator.get_steps())
    result = matched_step["func"](
        selected_stocks_yaml, indicator_config_yaml, matched_step["match"].groups()
    )
    print(result)
    # import re

    # text = "ignore ABB, BEL,TCS stocks"
    # pattern = r"^ignore (\w+(?:,*\s*\w*)*) stocks$"

    # match = re.search(pattern, text)
    # if match:
    #     extracted_string = match.group(1)
    #     print(extracted_string)
    # else:
    #     print("No match found.")

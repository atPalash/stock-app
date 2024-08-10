import pandas
from stock_app_py.utility.src.steps import then
from stock_app_py.system.src.steps import common


@then
def get_list(all_steps: list) -> dict:
    return {"tickers": all_steps[-1].result.pipe_tickers}


@then
def calculate(groups, query_df: pandas.DataFrame) -> pandas.DataFrame:
    logic = groups[0]
    # If logic was set earlier we ignore the earlier one, since the tickers should
    # be already filtered out with that logic.
    query_df["logic"] = None
    for index, row in query_df.iterrows():
        try:
            # Assume eval_expr is a string representing an evaluatable expression
            query_df.at[index, "logic"] = eval(logic, None, row.to_dict())
        except Exception as e:
            query_df.at[index, "error"] = (
                query_df.at[index, "error"] + f" then.calculate:{e.args}"
            )
    return query_df

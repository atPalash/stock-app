import pandas
from stock_app_py.utility.src.steps import then
from stock_app_py.system.src.steps import common


@then
def get_list(all_steps: list) -> dict:
    return {"tickers": all_steps[-1].result.pipe_tickers}


@then
def calculate(groups, query_df: pandas.DataFrame) -> pandas.DataFrame:
    """
    Applies the given logic to each row of the DataFrame and updates the DataFrame
    with the result.

    Args:
        col_name (str): The id of the list to be generated.
        logic (str): A string representing a Python expression to be evaluated on
                     each row of the DataFrame.
        query_df (pandas.DataFrame): The DataFrame containing the data to be processed.

    Returns:
        pandas.DataFrame: The updated DataFrame with a new column "logic" which
                          holds the result of the evaluated expression, and an
                          "error" column that logs any exceptions that occurred
                          during the evaluation.
    """
    col_name = groups[0]
    logic = groups[1]
    # logic = groups[0]
    # If logic was set earlier we ignore the earlier one, since the tickers should
    # be already filtered out with that logic.
    query_df[col_name] = None
    for index, row in query_df.iterrows():
        try:
            # Assume eval_expr is a string representing an evaluatable expression
            query_df.at[index, col_name] = eval(logic, None, row.to_dict())
        except Exception as e:
            query_df.at[index, "error"] = (
                query_df.at[index, "error"] + f" then.calculate:{e.args}"
            )
    return query_df

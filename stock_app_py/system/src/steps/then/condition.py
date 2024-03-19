import pandas
from stock_app_py.utility.src.steps import then
from stock_app_py.system.src.steps import common


@then
def calculate(groups, query_df: pandas.DataFrame) -> pandas.DataFrame:
    key, logic = groups
    query_df[key] = False
    for index, row in query_df.iterrows():
        try:
            # Assume eval_expr is a string representing an evaluatable expression
            query_df.at[index, f'{key}'] = eval(logic, None, row.to_dict())
        except Exception as e:
            query_df.at[index, 'error'] = query_df.at[index, "error"] + f" then.calculate:{e.args}"
    return query_df

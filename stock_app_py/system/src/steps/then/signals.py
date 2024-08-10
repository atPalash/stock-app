import pandas
from stock_app_py.utility.src.steps import then
from stock_app_py.system.src.steps import common

# TODO deprecate
@then
def list_stock_signals(all_steps: list) -> dict:
    """
    After generating signals from the when step, the condition of each ticker
    is filled with index and a boolean value signifying when the condition matches
    Here go through all the tickers and select those which satisfy the condition.

    Args:
        all_steps (list): all previous steps, will filter signals in each step.

    Returns:
        ret: {
            tickers: {
                ticker:[(index, condition)...]
            }
        }
    """
    try:
        ret = []
        tickers_with_signal = {}
        for step in all_steps:
            if step.type == "When " or step.parent == "when":
                for stp in step.result.data:
                    if any(
                        isinstance(item, tuple) and item[1] for item in stp["condition"]
                    ):
                        temp = {
                            "signal": stp["condition"],
                            "color": stp["color"],
                            "interval": stp["interval"],
                            "step": step.step,
                        }
                        if stp["ticker"] not in tickers_with_signal:
                            tickers_with_signal[stp["ticker"]] = [temp]
                        else:
                            tickers_with_signal[stp["ticker"]].append(temp)
        return {"tickers": list(tickers_with_signal), "signals": tickers_with_signal}
    except Exception as e:
        return {"exception": e.args}

@then
def calculate(groups, query_df: pandas.DataFrame) -> pandas.DataFrame:
    """
    Evaluates a logical expression on a DataFrame and stores the results.

    This function iterates through each row of the `query_df` DataFrame,
    evaluates a logical expression specified in `groups[0]` on the 'series' 
    column (which is itself a DataFrame), and stores the results in a new 
    column named '{logic}_signals'. If an error occurs during evaluation, it 
    appends the error message to the 'error' column of the `query_df` DataFrame.
    The idea is to append different signals as separate columns which can then
    be rendered by the client side.
    
    Args:
        groups (list): A list where the first element is a string representing 
                       a logical expression to be evaluated.
        query_df (pandas.DataFrame): A DataFrame with a 'series' column 
                                     containing nested DataFrames on which the 
                                     logical expression will be evaluated.

    Returns:
        pandas.DataFrame: The modified `query_df` DataFrame with an additional 
                          column in each nested DataFrame in 'series', and 
                          error messages if any evaluation fails.
    """
    logic = groups[1]
    col_name = groups[0]
    for index, row in query_df.iterrows():
        try:
            # Assume eval_expr is a string representing an evaluatable expression
            series_df = query_df.at[index, 'series']
            series_df[col_name] = None
            for inner_index, inner_row in series_df.iterrows():
                series_df.at[inner_index, col_name] = eval(logic, None, inner_row.to_dict())
            query_df.at[index, 'series'] = series_df
        except Exception as e:
            query_df.at[index, "error"] = (
                query_df.at[index, "error"] + f" then.calculate:{e.args}"
            )
    return query_df
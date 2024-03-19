import pandas
from stock_app_py.utility.src.path_helper import get_app_path
from stock_app_py.system.src.gherkin_generic_query import GherkinGenericQuery
from stock_app_py.system.src.command_handler import CommandHandler


def init(g_query: str):
    indicator_config_yaml = get_app_path("test_indicator.yaml")
    selected_stocks_yaml = get_app_path("selected_stocks.yaml")
    commandHandler = CommandHandler(
        selected_stocks_yaml, indicator_config_yaml=indicator_config_yaml
    )
    gherkin_query = GherkinGenericQuery(
        indicator_config_file=indicator_config_yaml,
        selected_stocks_config_file=selected_stocks_yaml,
        command_handler=commandHandler,
        parameter={"do": "get", "gherkin": g_query},
        name="",
    )
    abb_series = []
    tcs_series = []
    check = gherkin_query.execute()
    query_err = check.errors
    query_str = check.obj_as_string
    if query_err["error"] == "":
        query_df = check.obj["test"]["query_df"]
        abb_series = query_df[query_df["ticker"] == "ABB"]
        tcs_series = query_df[query_df["ticker"] == "TCS"]
    return (query_str, query_err, abb_series, tcs_series)


def test_gherkin_query_indicator():
    """Test a sample query that returns a pandas df without any errors.
    Test all the cols are availabel and check there values.
    """

    g_query = """Feature: v2
I want to query to get a list of turtle S1 stocks
Scenario: test
Given stocks ABB, TCS
When let atr14 = latest in 1 day close atr 14
* let close = latest in 1 day close
* let ema10 = latest in 1 day close ema 10
* let ema20 = latest in 1 day close ema 20
Then get tickers with (ema10 - ema20) < atr14 * 0.5
"""
    obj_str, err, abb_series, tcs_series = init(g_query=g_query)
    assert obj_str["test"] != ""
    assert err["error"] == ""
    assert abb_series["error"].values[0] == ""
    assert tcs_series["error"].values[0] == ""
    assert abb_series["atr14"].values[0] == 172.35
    assert tcs_series["atr14"].values[0] == 82.07
    assert abb_series["ema10"].values[0] == 5491.82
    assert tcs_series["ema10"].values[0] == 4074.28
    assert abb_series["ema20"].values[0] == 5240.30
    assert tcs_series["ema20"].values[0] == 4055.33
    assert abb_series["logic"].values[0] == False
    assert tcs_series["logic"].values[0] == True


def test_gherkin_query_ticker_rating():
    """Make a test query to find greatest movers in last n days. First, calculate
    ema / ma based on user input then get the slope (ema(latest - n) - ema(latest))
    / ema(latest)
    """
    g_query = """Feature: v2
Scenario: test
Given stocks ABB, TCS
When let ema10_change = change in 30 day close ema 10
Then get tickers with ema10_change > 0.1
"""
    obj_str, err, abb_series, tcs_series = init(g_query=g_query)
    assert obj_str["test"] != ""
    assert err["error"] == ""
    assert abb_series["error"].values[0] == ""
    assert tcs_series["error"].values[0] == ""
    assert abb_series["ema10_change"].values[0] == 0.15
    assert tcs_series["ema10_change"].values[0] == 0.06
    assert abb_series["logic"].values[0] == True
    assert tcs_series["logic"].values[0] == False


def test_gherkin_query_step_error():
    """Test an error in step statement"""
    err_step = "let rel_str  = latest in 60 day close rs_rating"
    g_query = f"""Feature: v2
I want to query to get a list of turtle S1 stocks
Scenario: test
Given stocks ABB, TCS
When {err_step}
* let atr14 = latest in 1 day close atr 14
* let close = latest in 1 day close
* let ema10 = latest in 1 day close ema 10
* let ema20 = latest in 1 day close ema 20
Then get tickers with (ema10 - ema20) < atr14 * 0.5
"""
    obj_str, err, _, _ = init(g_query=g_query)
    assert obj_str["test"] == "None"
    assert err["error"]["step"] == err_step


def test_gherkin_query_then_condition_extra_space():
    """Test an error in step statement"""
    # extra space in condition should fetch result
    err_step = "get tickers with (ema10   - ema20) < atr14 * 0.5"
    g_query = f"""Feature: v2
I want to query to get a list of turtle S1 stocks
Scenario: test
Given stocks ABB, TCS
When let atr14 = latest in 1 day close atr 14
* let ema10 = latest in 1 day close ema 10
* let ema20 = latest in 1 day close ema 20
Then {err_step}
"""
    obj_str, err, _, _ = init(g_query=g_query)
    assert obj_str["test"] != "None"
    assert err["error"] == ""


def test_gherkin_query_then_condition_error():
    """Test an error in step statement"""
    err_step = "get tickers with (ema10 - ema20) <* atr14 * 0.5"
    g_query = f"""Feature: v2
I want to query to get a list of turtle S1 stocks
Scenario: test
Given stocks ABB, TCS
When let atr14 = latest in 1 day close atr 14
* let ema10 = latest in 1 day close ema 10
* let ema20 = latest in 1 day close ema 20
Then {err_step}
"""
    obj_str, err, abb_series, tcs_series = init(g_query=g_query)
    assert (
        err["error"]
        == "('invalid syntax', ('<string>', 1, 18, '(ema10 - ema20) <* atr14 * 0.5', 1, 19))"
    )
    assert obj_str["test"] == "None"
    assert len(abb_series) == 0
    assert len(tcs_series) == 0


def test_gherkin_query_missing_col_name():
    """Test an error in step statement"""
    err_step = "get tickers with (ema10 - ema20) < atr14 * 0.5"
    g_query = f"""Feature: v2
I want to query to get a list of turtle S1 stocks
Scenario: test
Given stocks ABB, TCS
When let ema10 = latest in 1 day close ema 10
* let ema20 = latest in 1 day close ema 20
Then {err_step}
"""
    obj_str, err, abb_series, tcs_series = init(g_query=g_query)
    assert err["error"] == "(\"name 'atr14' is not defined\",)"
    assert obj_str["test"] == "None"
    assert len(abb_series) == 0
    assert len(tcs_series) == 0


# TODO fix this should return then step for user readability
def test_gherkin_query_error_let():
    """Test an error in then step statement"""
    err_step = "let close_ema20 = close 1> ema20"
    g_query = f"""Feature: v2
I want to query to get a list of turtle S1 stocks
Scenario: test
Given stocks ABB, TCS
When let atr14 = latest in 1 day close atr 14
* let ema10 = latest in 1 day close ema 10
* let ema20 = latest in 1 day close ema 20
* let close = latest in 1 day close
Then {err_step}
* let ema1020 = ema10 - ema20
* get tickers with ema1020 < atr14 * 0.5"
"""
    obj_str, err, abb_series, tcs_series = init(g_query=g_query)
    assert (
        err["error"]
        == "('invalid syntax', ('<string>', 1, 7, 'close 1> ema20', 1, 8)) then.calculate"
    )
    assert obj_str["test"] == "None"
    assert len(abb_series) == 0
    assert len(tcs_series) == 0

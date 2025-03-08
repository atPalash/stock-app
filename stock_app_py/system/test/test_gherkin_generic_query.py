import pandas
import stock_app_py.system.src.gherkin.gherkin_backtest as bt
from stock_app_py.system.src.gherkin.gherkin_backtest import GherkinBacktest
from stock_app_py.system.src.gherkin.gherkin_backtest_ohlc_helper import (
    GherkinBacktestOhlcHelper,
)
from stock_app_py.utility.src.path_helper import get_app_path
from stock_app_py.system.src.gherkin.gherkin_generic_query import GherkinGenericQuery
from stock_app_py.system.src.command_handler import CommandHandler


def init(g_query: str, interval: int, window: int, iterations: int):
    indicator_config_yaml = get_app_path("test_indicator.yaml")
    selected_stocks_yaml = get_app_path("selected_stocks.yaml")
    ut = GherkinBacktest(
        indicator_config_file=indicator_config_yaml,
        selected_stocks_config_file=selected_stocks_yaml,
        command_handler=None,
        parameter={
            "window": window,
            "interval": interval,
            "n": iterations,
            "gherkin": g_query,
        },
        name="",
    )
    results = ut.debug().obj
    return results


def test_backtest():
    """
    Test a basic test
    """
    g_query = f"""Feature: v2\n
    Scenario: {bt.SCENARIO}\n
    Given stocks from list ABB, TCS\n
    When let atr14change = rate in 20 samples of minute5 close atr 14\n
    * let ema10 = latest in 1 samples of minute5 close ema 10\n
    * let ema20 = latest in 1 samples of day close ema 20\n
    * let close = latest in 1 samples of minute5 close\n
    Then list bull = tickers with close > ema10 and close > ema20 and atr14change < 0
    * list bear = tickers with close < ema10 and close < ema20 and atr14change < 0
    """
    iterations = 2
    interval = "minute5"
    window = 40
    results = init(
        g_query=g_query, interval=interval, window=window, iterations=iterations
    )
    assert len(results) == iterations

    start_date = pandas.to_datetime(results[0]["start_date"][0])
    end_date = pandas.to_datetime(results[0]["end_date"][0])
    assert (end_date - start_date).seconds == 5 * window * 60


def test_positive_predictions():
    """
    Test a truth prediction
    """

    g_query = f"""Feature: v2\n
    Scenario: {bt.SCENARIO}\n
    Given stocks from list BHARTIARTL\n
    When let ema10Change = rate in 20 samples of minute5 close ema 10\n
    * let vwap10Change = rate in 20 samples of minute5 close vwap 10\n
    * let ema10Day = latest in 1 samples of day close ema 10\n
    * let close = latest in 1 samples of minute5 close\n
    Then let inrange = close > ema10Day * 0.99 and close < ema10Day * 1.01\n
    * list bull = tickers with ema10Change > 0 and vwap10Change > 0 and inrange\n
    * list bear = tickers with ema10Change < 0 and vwap10Change < 0 and inrange\n
    """
    iterations = 5
    results = init(
        g_query=g_query, interval="minute5", window=40, iterations=iterations
    )
    assert len(results) == iterations

    row = results[0]
    assert row["action"][0] == "bull"
    assert row["prediction"][0] == 1  # truth prediction
    assert row["gain%"][0] > 0


def test_negative_predictions():
    """
    Test a false prediction
    """

    g_query = f"""Feature: v2\n
    Scenario: {bt.SCENARIO}\n
    Given stocks from list BAJFINANCE\n
    When let ema10Change = rate in 20 samples of minute5 close ema 10\n
    * let vwap10Change = rate in 20 samples of minute5 close vwap 10\n
    * let ema10Day = latest in 1 samples of day close ema 10\n
    * let close = latest in 1 samples of minute5 close\n
    Then let inrange = close > ema10Day * 0.99 and close < ema10Day * 1.01\n
    * list bull = tickers with ema10Change > 0 and vwap10Change > 0 and inrange\n
    * list bear = tickers with ema10Change < 0 and vwap10Change < 0 and inrange\n
    """
    iterations = 5
    results = init(
        g_query=g_query, interval="minute5", window=40, iterations=iterations
    )
    assert len(results) == iterations

    row = results[0]
    assert row["action"][0] == "bear"
    assert row["prediction"][0] == 0  # false prediction
    assert row["gain%"][0] < 0


if __name__ == "__main__":
    test_backtest()

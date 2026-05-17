import asyncio
import copy

import pandas

from pytick.query.comparator import run
from pytick.query.query import QueryHandler
from pytick.test.utility import DummyQueryHandler
from pytick.query.trade import TradeHandler


def test_valid_gherkin():
    gherkin = """
Feature: v2
Scenario: test
Given stocks from index nifty50
When let ema10Day = latest in 1 samples of day close ema 10
* let close = latest in 1 samples of minute5 close
Then list bulls = tickers with close > ema10Day
"""
    is_valid, step_data, errors = QueryHandler.parse_gherkin(gherkin)
    assert is_valid
    assert isinstance(step_data, list) or isinstance(step_data, dict)
    assert errors == []


def test_missing_feature():
    gherkin = """
Scenario: test
Given stocks from index nifty50
"""
    is_valid, step_data, errors = QueryHandler.parse_gherkin(gherkin)
    assert not is_valid
    assert "Scenario found before Feature." in errors[0]


def test_invalid_step_order():
    gherkin = """
Feature: v2
Given stocks from index nifty50
Scenario: test
"""
    is_valid, step_data, errors = QueryHandler.parse_gherkin(gherkin)
    assert not is_valid
    assert "Given found before Scenario." in errors[0]


def test_invalid_step_keyword():
    gherkin = """
Feature: v2
Scenario: test
Foo something invalid
"""
    is_valid, step_data, errors = QueryHandler.parse_gherkin(gherkin)
    assert not is_valid


def test_invalid_variable_value():
    # This test assumes StepData and step regexes are set up to validate allowed values
    # You may need to adjust this test based on your StepData implementation
    gherkin = """
Feature: v2
Scenario: test
Given stocks from index invalid_index
"""
    is_valid, step_data, errors = QueryHandler.parse_gherkin(gherkin)
    assert not is_valid or errors, "Should fail for invalid variable value if StepData enforces allowed values."


def test_invalid_index():
    # This test assumes StepData and step regexes are set up to validate allowed values
    # You may need to adjust this test based on your StepData implementation
    gherkin = """
Feature: pytick llm  
Scenario: Test index not found error 
Given stocks from index nifty500  
When let ema100 = rate in 100 samples of day close ema 100  
* let ema200 = rate in 200 samples of day close ema 200  
* let close = latest in 1 samples of day close  
* let atr10 = latest in 1 samples of day close atr 10  
Then list bull = tickers with (ema100 > 0) & (ema200 > 0) & (abs(close - ema100) / ema100 < 4 * atr10)  
* list bear = tickers with (ema100 < 0) & (ema200 < 0) & (abs(close - ema100) / ema100 < 4 * atr10)
"""
    is_valid, step_data, errors = QueryHandler.parse_gherkin(gherkin)
    assert not is_valid or errors, "Should fail for invalid variable value if StepData enforces allowed values."


def test_notification():
    # This test assumes StepData and step regexes are set up to validate allowed values
    # You may need to adjust this test based on your StepData implementation
    gherkin = """
Feature: pytick llm  
Scenario: Test index not found error 
Given stocks from index nifty50  
When let ema10 = latest in 20 samples of minute5 close ema 10  
* let close = latest in 20 samples of minute5 close
* let notification = latest in 20 samples of minute5 notification
Then list bull = tickers with (close > ema10) & notification
* list bear = tickers with (close < ema10) & notification
"""
    is_valid, step_data, errors = QueryHandler.parse_gherkin(gherkin)
    assert is_valid or len(errors) > 0, f" Got errors: {errors}"
    expected_functions = {0: 'get_index_tickers', 1: 'calculate_indicators',
                          2: 'calculate_ohlc', 3: 'calculate_notification',
                          4: 'calculate_conditions', 5: 'calculate_conditions'}
    for i, v in expected_functions.items():
        function_name = step_data[i]['logic'].__name__
        assert function_name == v, f"Expected step {i} to use logic function '{v}' but got '{function_name}'"


def test_query_result():
    gherkin = """
Feature: pytick llm  
Scenario: Test RSI and EMA conditions
Given stocks from index nifty50  
When let ema10 = latest in 20 samples of minute5 close ema 10  
* let close = latest in 20 samples of minute5 close
* let rsi = latest in 20 samples of minute5 close rsi 14
Then list bull = tickers with (close > ema10) & rsi > 30 & rsi < 70 
* list bear = tickers with (close < ema10) & rsi > 70 & rsi < 30
"""
    handler = DummyQueryHandler().getQueryHandler()
    result = handler.get_gherkin_result(gherkin_str=gherkin)[1]
    bull = result[0]
    bear = result[1]
    expected_bull = {'bull': ['BEL', 'TCS', 'TMPV']}
    expected_bear = {'bear': []}
    assert isinstance(bull, dict), "Bull result should be a dict"
    assert isinstance(bear, dict), "Bear result should be a dict"
    assert bull == expected_bull, f"Expected bull result {expected_bull} but got {bull}"
    assert bear == expected_bear, f"Expected bear result {expected_bear} but got {bear}"


def test_ticker_list():
    # This test assumes StepData and step regexes are set up to validate allowed values
    # You may need to adjust this test based on your StepData implementation
    gherkin = """
Feature: pytick llm
Scenario: EMA10 and EMA20 rate analysis over 10 samples with close proximity and 0.5*ATR10
Given stocks from list BEL, INFY, TMPV, SBIN
When let ema10 = latest in 1 samples of day close ema 10
* let ema20 = latest in 1 samples of day close ema 20
* let ema10_rate = rate in 10 samples of day close ema 10
* let ema20_rate = rate in 10 samples of day close ema 20
* let close = latest in 1 samples of day close
* let atr10 = latest in 1 samples of day close atr 10
Then list buy = tickers with (ema10_rate > 0) & (ema20_rate > 0) & (abs(close - ema10) < 0.25 * atr10)
"""
    handler = DummyQueryHandler().getQueryHandler()
    result = handler.get_gherkin_result(gherkin_str=gherkin)[1]
    bull = result[0]
    expected_bull = {'buy': ['BEL']}
    assert isinstance(bull, dict), "Bull result should be a dict"
    assert bull == expected_bull, f"Expected bull result {expected_bull} but got {bull}"


def test_query_backtest():
    gherkin = """
Feature: pytick llm
Scenario: EMA10 and EMA20 rate analysis over 10 samples with close proximity and 0.5*ATR10
Given stocks from index nifty50
When let ema10 = latest in 1 samples of day close ema 10
* let ema20 = latest in 1 samples of day close ema 20
* let ema10_rate = rate in 10 samples of day close ema 10
* let ema20_rate = rate in 10 samples of day close ema 20
* let close = latest in 1 samples of day close
* let atr10 = latest in 1 samples of day close atr 10
Then list buy = tickers with (ema10_rate > 0) & (ema20_rate > 0) & (abs(close - ema10) < 0.5 * atr10)
* list sell = tickers with (ema10_rate < 0) & (ema20_rate < 0) & (abs(close - ema10) < 0.5 * atr10)
"""
    trade_handler = TradeHandler()
    query_handler = DummyQueryHandler().getQueryHandler()
    for itr in range(10, 0, -1):
        handler = copy.deepcopy(query_handler)
        handler.get_backtest_result(
            query=gherkin, trade_handler=trade_handler, window=itr, stop_loss_percent=1)
        # print(trade_handler.open_df)

    print(trade_handler.close_df)


def test_query_comparator():
    queries = [
    """
    Feature: pytick llm
    Scenario: KQ parabolic short setup analysis
    Given stocks from index nifty50
    When let close = latest in 1 samples of day close
    And let sma10 = latest in 1 samples of day close sma 10
    Then list sell = tickers with (close < sma10)
    """, 
    ]
    query_handler = DummyQueryHandler().getQueryHandler()
    async def disconnected():
        return False
    asyncio.run(run(disconnected= disconnected, query_handler=query_handler, queries=queries, start=2, stop=0, commission=0.01, timeout=10*60*60))
    

if __name__ == "__main__":
    test_query_comparator()

from pytick.query.query import QueryHandler

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
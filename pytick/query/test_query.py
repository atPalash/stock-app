from pytick.query.query import parse_gherkin

def test_valid_gherkin():
    gherkin = """
Feature: v2
Scenario: test
Given stocks from index nifty50
When let ema10Day = latest in 1 samples of day close ema 10
* let close = latest in 1 samples of minute5 close
Then list bulls = tickers with close > ema10Day
"""
    is_valid, step_data, errors = parse_gherkin(gherkin)
    assert is_valid
    assert isinstance(step_data, list) or isinstance(step_data, dict)
    assert errors == []

def test_missing_feature():
    gherkin = """
Scenario: test
Given stocks from index nifty50
"""
    is_valid, step_data, errors = parse_gherkin(gherkin)
    assert not is_valid
    assert "Scenario found before Feature." in errors[0]

def test_invalid_step_order():
    gherkin = """
Feature: v2
Given stocks from index nifty50
Scenario: test
"""
    is_valid, step_data, errors = parse_gherkin(gherkin)
    assert not is_valid
    assert "Given found before Scenario." in errors[0]

def test_invalid_step_keyword():
    gherkin = """
Feature: v2
Scenario: test
Foo something invalid
"""
    is_valid, step_data, errors = parse_gherkin(gherkin)
    assert not is_valid
    assert any("valid step keyword" in err for err in errors)

def test_invalid_variable_value():
    # This test assumes StepData and step regexes are set up to validate allowed values
    # You may need to adjust this test based on your StepData implementation
    gherkin = """
Feature: v2
Scenario: test
Given stocks from index invalid_index
"""
    is_valid, step_data, errors = parse_gherkin(gherkin)
    assert not is_valid or errors, "Should fail for invalid variable value if StepData enforces allowed values."

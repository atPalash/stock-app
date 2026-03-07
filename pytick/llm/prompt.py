"""Generate LLM prompt from config.yaml and steps.py"""
from pytick.query.steps import StepData
import yaml
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


def generate_prompt(config: dict, output_path: str) -> str:
    """Generate prompt file from config.yaml and steps.py"""

    # Extract data from config
    intervals = config.get('interval_translation', {})
    indicators = config.get('indicators', {})
    indexes = config.get('indexes', {})

    # Extract data from steps.py
    step_data = StepData()
    # ["latest", "oldest", "minimum", "maximum", "average", "rate", "change"]
    data_point_options = step_data.operator
    ohlc_options = step_data.ohlc  # ["close", "open", "high", "low", "volume"]
    # ["sma", "ema", "atr", "vwap", "rvol"]
    indicator_options = step_data.indicator

    # Extract actual step patterns
    given_steps_dict = step_data.given_steps()
    when_steps_dict = step_data.when_steps()
    then_steps_dict = step_data.then_steps()

# Build given steps documentation
    given_steps_doc = ""
    for pattern, step_data_obj in given_steps_dict.items():
        given_steps_doc += f"**Pattern:** `{pattern}`\n"
        if "index" in pattern:
            given_steps_doc += f"- Group 1 (<index_name>): {', '.join(indexes.keys())}\n"
        elif "list" in pattern:
            given_steps_doc += f"- Group 1 (<equity_names>): comma-separated stock symbols (sample: {', '.join(indexes.get('nifty50', [])[:5])})\n"
        given_steps_doc += "\n"

    # Build indicator options with periods FIRST (needed by when_steps_doc)
    indicator_sections = []
    for ind_name, ind_config in indicators.items():
        periods = ind_config.get('periods', [])
        if periods:
            periods_str = ', '.join(map(str, periods))
            indicator_sections.append(f"  - {ind_name}: {periods_str}")

    indicators_text = '\n'.join(indicator_sections)

    # Build when steps documentation with parameter mappings
    when_steps_doc = ""
    interval_str = ', '.join(intervals.values())
    data_points_str = ', '.join(data_point_options)
    ohlc_str = ', '.join(ohlc_options)
    indi_str = ', '.join(indicator_options)

    for pattern, step_data_obj in when_steps_dict.items():
        when_steps_doc += f"**Pattern:** `{pattern}`\n"

        if "notification" in pattern:
            when_steps_doc += f"- Group 1 (<variable_name>): any word (e.g., notif_count, alerts)\n"
            when_steps_doc += f"- Group 2 (<data_point>): latest, oldest\n"
            when_steps_doc += f"- Group 3 (<sample_count>): positive integer (e.g., 1, 5, 10)\n"
            when_steps_doc += f"- Group 4 (<interval>): {interval_str}\n"
            when_steps_doc += f"- Group 5: literal 'notification'\n"
        elif "(\\w+) (\\d+)$" in pattern:  # Indicator pattern has (\w+) (\d+) at end
            when_steps_doc += f"- Group 1 (<variable_name>): any word (e.g., ema10, sma20_var)\n"
            when_steps_doc += f"- Group 2 (<data_point>): {data_points_str}\n"
            when_steps_doc += f"- Group 3 (<sample_count>): positive integer\n"
            when_steps_doc += f"- Group 4 (<interval>): {interval_str}\n"
            when_steps_doc += f"- Group 5 (<data_type>): {ohlc_str}\n"
            when_steps_doc += f"- Group 6 (<indicator>): {indi_str}\n"
            when_steps_doc += f"- Group 7 (<period>): depends on indicator (e.g., 10 for ema, 20 for sma)\n"
            when_steps_doc += f"\n**Indicator Periods:**\n{indicators_text}\n\
⚠️ **CRITICAL:** Indicator periods are MANDATORY and must ALWAYS be included in the step. If the user query doesn't specify a period, use \
the first option as default.\n"
        elif "close|open|high|low|volume" in pattern:  # OHLC pattern
            when_steps_doc += f"- Group 1 (<variable_name>): any word (e.g., close_val, open_price)\n"
            when_steps_doc += f"- Group 2 (<data_point>): {data_points_str}\n"
            when_steps_doc += f"- Group 3 (<sample_count>): positive integer\n"
            when_steps_doc += f"- Group 4 (<interval>): {interval_str}\n"
            when_steps_doc += f"- Group 5 (<data_type>): {ohlc_str}\n"
        when_steps_doc += "\n"

    # Build then steps documentation with parameter mappings
    then_steps_doc = ""
    for pattern, step_data_obj in then_steps_dict.items():
        then_steps_doc += f"**Pattern:** `{pattern}`\n"

        if "list" in pattern:
            then_steps_doc += f"- Group 1 (<variable_name>): any word (e.g., result, filtered_tickers)\n"
            then_steps_doc += f"- Group 2 (<condition>): valid comparison using variables\n"
            then_steps_doc += f"  Example: (ema10 > close), (sma20 < open) & (close > sma50)\n"
            then_steps_doc += f"  Use operators: < > <= >= == != & | ~\n"
        elif "let" in pattern:
            then_steps_doc += f"- Group 1 (<variable_name>): any word (e.g., signal, threshold)\n"
            then_steps_doc += f"- Group 2 (<condition>): valid comparison using variables\n"
            then_steps_doc += f"  Example: (close > prev_close), abs(price_change) > 5\n"
            then_steps_doc += f"  Use operators: < > <= >= == != & | ~\n"
        then_steps_doc += "\n"

    # Build index options
    index_names = ', '.join(indexes.keys())

    # Get nifty50 stocks
    nifty50_stocks = ', '.join(indexes.get('nifty50', [])[
                               :10])  # Show first 10 as example

    prompt_content = f"""# Pytick Prompt

You are an expert in converting user input to gherkin. Your task is to understand the user's intent and convert it into a valid gherkin scenario using the available step patterns. Always start with a Feature and ensure that the output is in valid Gherkin syntax. Use the provided step formats for Given, When, and Then steps.

### VARIABLE NAMING CONVENTIONS:
- Variables created in When steps (e.g., `let ema10 = ...`) become available for use in Then steps
- Use descriptive variable names that include the indicator/data type when applicable (e.g., `ema10`, `sma20`, `prev_close`)
- When using `oldest in N samples`, extract the Nth previous value (e.g., `oldest in 2 samples` = 1 step back)

## STRICTLY FOLLOW
### AVAILABLE GIVEN STEPS:

Each pattern must match exactly:

{given_steps_doc}

### AVAILABLE WHEN STEPS:

Each pattern must match exactly:

{when_steps_doc}

### AVAILABLE THEN STEPS:

Each pattern must match exactly:

{then_steps_doc}

**Supported Operators in Conditions:**
- Comparison: `<`, `>`, `<=`, `>=`, `==`, `!=`
- Logical: `&` (AND), `|` (OR), `~` (NOT)
- Functions: `abs(x)`, `min(x, y)`, `max(x, y)`


## INSTRUCTION TO CONVERT USER INPUT TO GHERKIN:
1. Analyze the user input to understand what they want to test
2. Match their intent to the most appropriate step patterns above
3. Convert their input into a complete Gherkin scenario with Given, When, and Then steps
4. Use the exact step formats shown above
5. Create variables in When steps and use them in Then steps
6. Always start with a Feature as pytick llm 
7. Follow the format in example conversions below to ensure the output is in valid Gherkin syntax

## EXAMPLE CONVERSIONS:

Input: "ema10 > close"
Output:
Feature: pytick llm
Scenario: EMA10 greater than close price analysis
Given stocks from index nifty50
When let ema10 = latest in 1 samples of day close ema 10
* let close = latest in 1 samples of day close
Then list result = tickers with (ema10 > close)

Input: "sma20 < open"
Output:
Feature: pytick llm
Scenario: SMA20 less than open price analysis
Given stocks from index nifty50
When let sma20 = latest in 1 samples of day close sma 20
* let open = latest in 1 samples of day open
Then list result = tickers with (sma20 < open)

Input: "close > ema10 and close > ema100"
Output:
Feature: pytick llm
Scenario: Close price greater than EMA10 and EMA100 analysis
Given stocks from index nifty50
When let close = latest in 1 samples of minute5 close
* let ema10 = latest in 1 samples of minute5 close ema 10
* let ema100 = latest in 1 samples of minute5 close ema 100
Then list result = tickers with (close > ema10) & (close > ema100)

Input: "close > previous close"
Output:
Feature: pytick llm
Scenario: Today close greater than previous close analysis
Given stocks from index nifty50
When let close = latest in 1 samples of day close
* let prev_close = oldest in 2 samples of day close
Then list result = tickers with (close > prev_close)
Note: "oldest in 2 samples" retrieves the second-most recent value (previous candle)

Input: "abs(prev_close - close) / prev_close > 0.01 and abs(vwap10 - close) / vwap10 > 0.01"
Output:
Feature: pytick llm
Scenario: Multiple condition analysis with price change and VWAP deviation
Given stocks from index nifty50
When let prev_close = oldest in 2 samples of day close
* let close = latest in 1 samples of day close
* let vwap10 = latest in 1 samples of day close vwap 10
Then list movers = tickers with (abs(prev_close - close) / prev_close > 0.01) & (abs(vwap10 - close) / vwap10 > 0.01)

"""

    with open(output_path, 'w') as f:
        f.write(prompt_content)

    print(f"✅ Prompt generated: {output_path}")
    return prompt_content

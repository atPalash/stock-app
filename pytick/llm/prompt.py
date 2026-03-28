"""Generate prompt files from config.yaml and steps.py."""
from pytick.query.steps import StepData
from pytick.bot.discordbot import DiscordBot
import yaml
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


def generate_prompt(
    config: dict,
    output_init_prompt: str,
    output_retry_prompt: str,
    output_getting_started: str,
):
    """Generate LLM prompts and Discord join message prompt."""

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
            indicator_sections.append(f"* {ind_name}: {periods_str}")

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
            # when_steps_doc += f"- Defaults:<data_point> - latest, <sample_count> - 1, <interval> - day\n"
        elif "(\\w+) (\\d+)$" in pattern:  # Indicator pattern has (\w+) (\d+) at end
            when_steps_doc += f"- Group 1 (<variable_name>): any word (e.g., ema10, sma20_var)\n"
            when_steps_doc += f"- Group 2 (<data_point>): {data_points_str}\n"
            when_steps_doc += f"- Group 3 (<sample_count>): positive integer\n"
            when_steps_doc += f"- Group 4 (<interval>): {interval_str}\n"
            when_steps_doc += f"- Group 5 (<ohlc>): {ohlc_str}\n"
            when_steps_doc += f"- Group 6 (<indicator>): {indi_str}\n"
            when_steps_doc += f"- Group 7 (<period>): depends on indicator (e.g., 10 for ema, 20 for sma)\n"
            # when_steps_doc += f"- Defaults:<data_point> - latest, <sample_count> - 1, <interval> - day, <ohlc>-close, <indicator>-ema\n"
            when_steps_doc += f"\n**Indicator Periods:**\n{indicators_text}\n\
⚠️ **CRITICAL:** Indicator periods are MANDATORY and must ALWAYS be included in the step. If the user query doesn't specify a period, use \
the first option as default.\n"
        elif "close|open|high|low|volume" in pattern:  # OHLC pattern
            when_steps_doc += f"- Group 1 (<variable_name>): any word (e.g., close_val, open_price)\n"
            when_steps_doc += f"- Group 2 (<data_point>): {data_points_str}\n"
            when_steps_doc += f"- Group 3 (<sample_count>): positive integer\n"
            when_steps_doc += f"- Group 4 (<interval>): {interval_str}\n"
            when_steps_doc += f"- Group 5 (<ohlc>): {ohlc_str}\n"
            # when_steps_doc += f"- Defaults:<data_point> - latest, <sample_count> - 1, <interval> - day, <ohlc>-close\n"
        when_steps_doc += f"\n"

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

    starting_prompt = f"""# Pytick Prompt

You are an expert in converting user input to gherkin. Your task is to understand the user's intent and convert it into a valid gherkin scenario using the available step patterns. Always start with a Feature and ensure that the output is in valid Gherkin syntax. Use the provided step formats for Given, When, and Then steps.
"""
    starting_instruction = f"""## INSTRUCTION TO CONVERT USER INPUT TO GHERKIN:
1. Analyze the user input to understand what they want to test
2. Match their intent to the most appropriate step patterns above
3. Convert their input into a complete Gherkin scenario with Given, When, and Then steps
4. Use the exact step formats shown above, MUST ENSURE all the groups for a pattern are filled
5. Create variables in When steps and use them in Then steps
6. Always start with a Feature as pytick llm
7. Follow the format in example conversions below to ensure the output is in valid Gherkin syntax"""
    starting_examples = f"""## EXAMPLE CONVERSIONS:

Input: "ema10 > close"
Output:
Feature: pytick llm
Scenario: EMA10 greater than close price analysis
Given stocks from index nifty50
When let ema10 = latest in 1 samples of day close ema 10
And let close = latest in 1 samples of day close
Then list result = tickers with (ema10 > close)

Input: "close > ema10 and close > ema100"
Output:
Feature: pytick llm
Scenario: Close price greater than EMA10 and EMA100 analysis
Given stocks from index nifty50
When let close = latest in 1 samples of minute5 close
And let ema10 = latest in 1 samples of minute5 close ema 10
And let ema100 = latest in 1 samples of minute5 close ema 100
Then list result = tickers with (close > ema10) & (close > ema100)

Input: "close > previous close"
Output:
Feature: pytick llm
Scenario: Today close greater than previous close analysis
Given stocks from index nifty50
When let close = latest in 1 samples of day close
And let prev_close = oldest in 2 samples of day close
Then list result = tickers with (close > prev_close)
Note: "oldest in 2 samples" retrieves the second-most recent value (previous candle)

Input: "abs(prev_close - close) / prev_close > 0.01 and abs(vwap10 - close) / vwap10 > 0.01"
Output:
Feature: pytick llm
Scenario: Multiple condition analysis with price change and VWAP deviation
Given stocks from index nifty50
When let prev_close = oldest in 2 samples of day close
And let close = latest in 1 samples of day close
And let vwap10 = latest in 1 samples of day close vwap 10
Then list movers = tickers with (abs(prev_close - close) / prev_close > 0.01) & (abs(vwap10 - close) / vwap10 > 0.01)
"""

    retry_prompt = f"""# chattick Prompt - Fix gherkin errors

The gherkin scenario has errors. Please fix the errors and ensure the output is in valid Gherkin syntax. Follow the step patterns exactly as shown below and use the provided examples as a guide."""
    retry_instruction = f"""## INSTRUCTION TO FIX GHERKIN ERRORS:
1. Analyze the gherkin scenario and identify syntax errors or mismatches with step patterns
2. Refer to the step patterns and ensure each step in the scenario matches one of the patterns exactly
and the all the groups are filled
3. Correct any syntax errors (e.g., missing keywords, incorrect variable usage)
4. Ensure the scenario starts with a Feature and follows the Given-When-Then structure
5. Use the example conversions as a guide to ensure the output is in valid Gherkin syntax"""
    retry_examples = f"""## EXAMPLE FIXES:

Input: Feature: pytick llm
Scenario: Multiple condition analysis with price change and VWAP deviation
Given stocks from index nifty50
When let prev_close = oldest in 2 samples of day close
And let close = latest in 1 samples of day close
And let vwap = latest in 1 samples of day close vwap
Then list movers = tickers with (abs(prev_close - close) / prev_close > 0.01) & (abs(vwap10 - close) / vwap10 > 0.01)
Output:
Feature: pytick llm
Scenario: Multiple condition analysis with price change and VWAP deviation
Given stocks from index nifty50
When let prev_close = oldest in 2 samples of day close
And let close = latest in 1 samples of day close
And let vwap10 = latest in 1 samples of day close vwap 10
Then list movers = tickers with (abs(prev_close - close) / prev_close > 0.01) & (abs(vwap10 - close) / vwap10 > 0.01)
Fix:
vwap is an indicator that requires a period (e.g., vwap10). The step must specify the indicator and period to match the when step pattern for indicators.
The variable name in the condition must also be updated to match the variable created in the When step (vwap10 instead of vwap).

Input: Here is the updated
Feature: pytick llm
Scenario: Multiple condition analysis with price change and VWAP deviation
Given stocks from index nifty50
When let prev_close = oldest in 2 samples of day close
And let close = latest in 1 samples of day close
Then list movers = tickers with close > prev_close
Output:
Feature: pytick llm
Scenario: Multiple condition analysis with price change and VWAP deviation
Given stocks from index nifty50
When let prev_close = oldest in 2 samples of day close
And let close = latest in 1 samples of day close
Then list movers = tickers with close > prev_close
Fix:
Remove the greeting "Here is the updated" which is not part of valid Gherkin syntax. The rest of the scenario is already in valid Gherkin format and matches the step patterns, so no other changes are needed.
"""

    def get_prompt_content(prompt, instruction, examples, output_path):

        prompt_content = f"""{prompt}

### VARIABLE NAMING CONVENTIONS:
- Variables created in When steps (e.g., `let ema10 = ...`) become available for use in Then steps
- Use descriptive variable names that include the indicator/data type when applicable (e.g., `ema10`, `sma20`, `prev_close`)
- When using `oldest in N samples`, extract the Nth previous value (e.g., `oldest in 2 samples` = 1 step back)

### STRICTLY FOLLOW
### AVAILABLE GIVEN STEPS:

Each pattern must match exactly:

{given_steps_doc}

### AVAILABLE WHEN STEPS:

Each pattern must match exactly:

{when_steps_doc}

### TIMEFRAME CONSISTENCY RULES:
- All `When` steps in one scenario MUST use the same `<interval>` token.
- If any `When` step uses `minute5`, all `When` steps must use `minute5` (same for `day`, `week`, etc.).
- Only allow mixed intervals when the user explicitly asks for multiple timeframes (example: "compare day EMA with minute5 close").
- If user does not specify interval, choose one default interval and use it for every `When` step in that scenario.

### AVAILABLE THEN STEPS:

Each pattern must match exactly:

{then_steps_doc}

**Supported Operators in Conditions:**
- Comparison: `<`, `>`, `<=`, `>=`, `==`, `!=`
- Logical: `&` (AND), `|` (OR), `~` (NOT)
- Functions: `abs(x)`, `min(x, y)`, `max(x, y)`

{instruction}

{examples}
"""

        with open(output_path, 'w') as f:
            f.write(prompt_content)

        # print(f"✅ Prompt generated: {output_path}")

    # Generate initial prompt
    get_prompt_content(
        starting_prompt, starting_instruction, starting_examples, output_init_prompt)
    # Generate retry prompt
    get_prompt_content(retry_prompt, retry_instruction,
                       retry_examples, output_retry_prompt)

    # Getting started
    getting_started = f"""🎉 Welcome to chattick! 🇮🇳

Hey there 👋 — awesome to have you with us! chattick turns your trading ideas into structured, ready‑to‑run scenarios — instantly.

📥 Check your inbox: All bot conversations happen in direct message

💬 Try simple ideas:
ema10 > close
close > previous close
sma20 < open

🧩 Quick Reference
indexes: {index_names}
Indicators:\n{indicators_text}\n
Intervals: {interval_str}

⚙️ Slash Commands:
</query run:1480627118227460210> → Run a single query
</query subscribe:1480627118227460210> → Subscribe to live query results
</query subscribe_ls:1480627118227460210> → List your active subscriptions
</query unsubscribe:1480627118227460210>→ Stop a subscription

📚 Explore:
See working examples in #examples
See demos in  #demos
Copy prompt from #prompt

🚀 Ready? Start testing your first idea!
"""
    with open(os.path.join(config.get('app_data_path', ''), output_getting_started), "w") as f:
        f.write(getting_started)

    # Rules
    rules = f""":scroll: chattick Server Rules

No financial advice — the bot helps generate logic, not market recommendations.

Use the bot properly — don’t spam or flood the bot with random text.

No misuse or exploits — don’t attempt to break, overload, or bypass the bot’s logic.

Report issues responsibly —
:lady_beetle: For bugs → Post in #bug-reports or tag @admin
:bulb: For new features or ideas → Use #feature-requests 

Respect others — no harassment, hate speech, or off-topic arguments.

Stay organized — Your interaction with bot happens in direct message.
"""
    with open(os.path.join(config.get('app_data_path', ''), "rules.md"), "w") as f:
        f.write(rules)

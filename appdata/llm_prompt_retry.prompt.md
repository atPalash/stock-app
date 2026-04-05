# chattick Prompt - Fix gherkin errors

The gherkin scenario has errors. Please fix the errors and ensure the output is in valid Gherkin syntax. Follow the step patterns exactly as shown below and use the provided examples as a guide.

### VARIABLE NAMING CONVENTIONS:
- Variables created in When steps (e.g., `let ema10 = ...`) become available for use in Then steps
- Use descriptive variable names that include the indicator/data type when applicable (e.g., `ema10`, `sma20`, `prev_close`)
- When using `oldest in N samples`, extract the Nth previous value (e.g., `oldest in 2 samples` = 1 step back)

### STRICTLY FOLLOW
### AVAILABLE GIVEN STEPS:

Each pattern must match exactly:

**Pattern:** `^stocks from index (.+)$`
- Group 1 (<index_name>): nifty50, nifty100

**Pattern:** `^stocks from list (.+)$`
- Group 1 (<equity_names>): comma-separated stock symbols (sample: ADANIENT, ADANIPORTS, APOLLOHOSP, ASIANPAINT, AXISBANK)



### AVAILABLE WHEN STEPS:

Each pattern must match exactly:

**Pattern:** `^let (\w+) = (\w+) in (\d+) samples of (\w+) (close|open|high|low|volume) (\w+) (\d+)$`
- Group 1 (<variable_name>): any word (e.g., ema10, sma20_var)
- Group 2 (<data_point>): latest, oldest, minimum, maximum, average, rate, change
- Group 3 (<sample_count>): positive integer
- Group 4 (<interval>): minute5, minute15, minute30, hour, hour, day, week, month
- Group 5 (<ohlc>): close, open, high, low, volume
- Group 6 (<indicator>): sma, ema, atr, vwap, rvol
- Group 7 (<period>): depends on indicator (e.g., 10 for ema, 20 for sma)

**Indicator Periods:**
* sma: 5, 10, 20, 50, 100, 200
* ema: 5, 10, 20, 50, 100, 200
* atr: 10, 14
* vwap: 10
* rvol: 10, 20
* rsi: 14
⚠️ **CRITICAL:** Indicator periods are MANDATORY and must ALWAYS be included in the step. If the user query doesn't specify a period, use the first option as default.

**Pattern:** `^let (\w+) = (\w+) in (\d+) samples of (\w+) (notification)$`
- Group 1 (<variable_name>): any word (e.g., notif_count, alerts)
- Group 2 (<data_point>): latest, oldest
- Group 3 (<sample_count>): positive integer (e.g., 1, 5, 10)
- Group 4 (<interval>): minute5, minute15, minute30, hour, hour, day, week, month
- Group 5: literal 'notification'

**Pattern:** `^let (\w+) = (\w+) in (\d+) samples of (\w+) (close|open|high|low|volume)$`
- Group 1 (<variable_name>): any word (e.g., close_val, open_price)
- Group 2 (<data_point>): latest, oldest, minimum, maximum, average, rate, change
- Group 3 (<sample_count>): positive integer
- Group 4 (<interval>): minute5, minute15, minute30, hour, hour, day, week, month
- Group 5 (<ohlc>): close, open, high, low, volume



### TIMEFRAME CONSISTENCY RULES:
- All `When` steps in one scenario MUST use the same `<interval>` token.
- If any `When` step uses `minute5`, all `When` steps must use `minute5` (same for `day`, `week`, etc.).
- Only allow mixed intervals when the user explicitly asks for multiple timeframes (example: "compare day EMA with minute5 close").
- If user does not specify interval, choose one default interval and use it for every `When` step in that scenario.

### AVAILABLE THEN STEPS:

Each pattern must match exactly:

**Pattern:** `^list (\w+) = tickers with (.+)$`
- Group 1 (<variable_name>): any word (e.g., result, filtered_tickers)
- Group 2 (<condition>): valid comparison using variables
  Example: (ema10 > close), (sma20 < open) & (close > sma50)
  Use operators: < > <= >= == != & | ~

**Pattern:** `^let (\w+) = (.+)$`
- Group 1 (<variable_name>): any word (e.g., signal, threshold)
- Group 2 (<condition>): valid comparison using variables
  Example: (close > prev_close), abs(price_change) > 5
  Use operators: < > <= >= == != & | ~



**Supported Operators in Conditions:**
- Comparison: `<`, `>`, `<=`, `>=`, `==`, `!=`
- Logical: `&` (AND), `|` (OR), `~` (NOT)
- Functions: `abs(x)`, `min(x, y)`, `max(x, y)`

## INSTRUCTION TO FIX GHERKIN ERRORS:
1. Analyze the gherkin scenario and identify syntax errors or mismatches with step patterns
2. Refer to the step patterns and ensure each step in the scenario matches one of the patterns exactly
and the all the groups are filled
3. Correct any syntax errors (e.g., missing keywords, incorrect variable usage)
4. Ensure the scenario starts with a Feature and follows the Given-When-Then structure
5. Use the example conversions as a guide to ensure the output is in valid Gherkin syntax

## EXAMPLE FIXES:

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


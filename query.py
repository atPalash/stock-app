import logging
import re

from utility import get_logger
from steps import StepData

logger = get_logger(__name__, logging.DEBUG)

def __validate_step_order(lines, errors):
    feature_found = False
    scenario_found = False
    given_found = False
    when_found = False
    then_found = False
    for line in lines:
        if line.startswith('Feature:'):
            feature_found = True
            continue
        elif line.startswith('Scenario:'):
            scenario_found = True
            if not feature_found:
                errors.append("Scenario found before Feature.")
                return False
            continue
        elif line.startswith('Given'):
            given_found = True
            if not feature_found or not scenario_found:
                errors.append("Given found before Scenario.")
                return False
        elif line.startswith('When'):
            when_found = True
            if not feature_found or not scenario_found or not given_found:
                errors.append("When found before Scenario or Given.")
                return False
        elif line.startswith('Then'):
            then_found = True
            if not feature_found or not scenario_found or not when_found or not given_found:
                errors.append("Then found before Scenario or When.")
                return False
    return True

def __fetch_step_data(lines, errors):
    step_data = StepData()
    step_patterns =  {
        'Given': step_data.given_steps(),
        'When': step_data.when_steps(),
        'Then': step_data.then_steps()
    }
    conjunctions = ['And', '*']
    match_values = []
    for line_unfiltered in lines:
        line = re.sub(r'\s+', ' ', line_unfiltered).strip()
        matched = False
        if any(line.startswith(prefix) for prefix in ['Feature:', 'Scenario:']):
            matched = True
            continue
        step_split = line.split(' ')
        current_step = current_step if step_split[0] in conjunctions else step_split[0]
        if current_step not in step_patterns.keys():
            errors.append(f"Line does not start with a valid step keyword: {line}")
            return False, match_values
        line_step = ' '.join(step_split[1:])
        for regex, step_data in step_patterns[current_step].items():
            match_obj = re.match(regex, line_step)
            if match_obj:
                variable_indexes = list(step_data.variables.keys())
                matches = []
                for i in range(1, len(match_obj.groups()) + 1):
                    value = match_obj.group(i)
                    allowed_values = step_data.variables.get(variable_indexes[i-1], None)
                    if allowed_values and '<' not in allowed_values[0] and '>' not in allowed_values[0]:
                        if value not in allowed_values:
                            errors.append(f"Invalid value '{value}' for variable '{variable_indexes[i-1]}' in line: '{line_unfiltered}'. Allowed values: {allowed_values}")
                            return False, match_values
                    matches.append({'index': variable_indexes[i-1], 'value': value})
                match_values.append({'statement': line_unfiltered, 'regex': regex, 'values': matches})
                matched = True
        if not matched:
            errors.append(f"Line does not start with a valid step keyword: {line}")
    return len(errors) == 0, match_values

        
def parse_gherkin(gherkin_str):
    """
    Validates that the Gherkin string contains only Given, When, Then steps in correct order.
    Returns (True, []) if valid, (False, [error messages]) otherwise.
    """
    lines = [line.strip() for line in gherkin_str.strip().splitlines() if line.strip()]
    errors = []
    if not __validate_step_order(lines, errors):
        return False, {}, errors
    success, step_data = __fetch_step_data(lines, errors)
    if not success:
        return False, {}, errors
    return True, step_data, errors


if __name__ == "__main__":
    gherkin = """
Feature: v2
Scenario: test
Given stocks from index nifty50
When let ema10Day = latest in 1 samples of 1 day close ema 10
* let close = latest in 1 samples of minute5 close
Then list bulls = tickers with close > ema10Day
"""
    is_valid, step_data, errors = parse_gherkin(gherkin)
    print(f"Gherkin is valid: {is_valid}")
    if not is_valid:
        print("Errors:")
        for err in errors:
            print(err)
    else:
        print("Parsed Step Data:")
        for step in step_data:
            print(step)

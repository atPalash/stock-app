import logging
import os
import re

from fastapi.params import Query
import pandas

# from utility.utility import get_logger
from pytick.dataframe.dataframe import DataFrameHandler
from pytick.query.steps import StepData
from pytick.utility.utility import get_logger, read_config

logger = get_logger(__name__, logging.DEBUG)

class QueryHandler:
    def __init__(self, data_handler: DataFrameHandler):
        self.data_handler = data_handler

    @staticmethod
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

    @staticmethod
    def __fetch_step_data(lines:list)-> tuple[bool, list]:
        errors = []
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
                    match_values.append({'statement': line_unfiltered, 'regex': regex, 'values': matches, 'step': current_step, 'logic': step_data.logic})
                    matched = True
            if not matched:
                errors.append(f"Regex match for \"{line}\" not found in {list(step_patterns[current_step].keys())}")
        return len(errors) == 0, match_values

    @staticmethod
    def __parse_gherkin(gherkin_str:str)-> tuple[bool, dict, list]:
        """
        Validates that the Gherkin string contains only Given, When, Then steps in correct order.
        Returns (True, []) if valid, (False, [error messages]) otherwise.
        """
        lines = [line.strip() for line in gherkin_str.strip().splitlines() if line.strip()]
        errors = []
        if not QueryHandler.__validate_step_order(lines, errors):
            return False, {}, errors
        success, step_data = QueryHandler.__fetch_step_data(lines)
        if not success:
            return False, {}, errors
        return True, step_data, errors
    
    def __process_given_steps(self, given_steps:list)-> tuple[bool, list, list]:
        tickers = []
        for step in given_steps:
            values = [v['value'] for v in step.get('values', [])]
            kwargs = {"tickers": values[0]}
            success, tickers, errors = step.get('logic')(**kwargs)
            if not success:
                logger.error(f"Error getting tickers: {errors}")
        if tickers is None or len(tickers) == 0:
            logger.error("No tickers found from Given steps.")
            return False, {}, errors
        return True, tickers, []

    def __process_when_steps(self, when_steps:list, given_result:list) -> tuple[bool, pandas.DataFrame, list]:
        result = pandas.DataFrame(columns=['ticker'])
        for step in when_steps:
            values = [v['value'] for v in step.get('values', [])]
            if step['logic'].__qualname__ == 'calculate_indicators':
                id, operator, query_span, interval, ohlc_source, indicator, window = values
                kwargs = {'id': id, 'operator': operator, 'query_span': query_span, 'ohlc_source': ohlc_source, 'indicator': indicator, 'window': window}
            if step['logic'].__qualname__ == 'calculate_ohlc':
                id, operator, query_span, interval, ohlc_source = values
                kwargs = {'id': id, 'operator': operator, 'query_span': query_span, 'ohlc_source': ohlc_source}

            # Add column if it doesn't exist
            if id not in result.columns:
                result[id] = None
            
            for ticker in given_result:
                # Add row for ticker if it doesn't exist
                if ticker not in result['ticker'].values:
                    new_row = {'ticker': ticker}
                    result = pandas.concat([result, pandas.DataFrame([new_row])], ignore_index=True)
                
                df = self.data_handler.get_tables(tickers=[ticker], interval='1d').get('data', {}).get(ticker, None)
                if df is None or df.empty:
                    logger.error(f"No data found for ticker {ticker} with interval {interval}")
                    continue
                success, val, errors = step.get('logic')(df, **kwargs)
                result.loc[result['ticker'] == ticker, id] = val
                if not success:
                    logger.error(f"Error calculating variables: {errors}")
                    return False, {}, errors
        return True, result, []

    def __process_then_steps(self, then_steps:list, when_results:pandas.DataFrame) -> tuple[bool, pandas.DataFrame, list]:
        result = when_results
        for step in then_steps:
            values = [v['value'] for v in step.get('values', [])]
            id, condition = values
            kwargs = {'id': id, 'condition': condition}
            success, result, errors = step.get('logic')(when_results,**kwargs)
            if not success:
                logger.error(f"Error calculating Then step: {errors}")
                return False, {}, errors

        return True, result, []

    def get_gherkin_result(self, gherkin_str:str) -> tuple[bool, dict, list]:
        is_valid, step_data, errors = QueryHandler.__parse_gherkin(gherkin_str)
        if not is_valid:
            return False, {}, errors
        
        given_steps = [step for step in step_data if step.get('step') == 'Given']
        when_steps = [step for step in step_data if step.get('step') == 'When']
        then_steps = [step for step in step_data if step.get('step') == 'Then']

        # Process Given steps to get tickers
        success, tickers, errors = self.__process_given_steps(given_steps)
        if not success:
            return False, {}, errors
        # Process When steps to calculate variables
        success, when_results, errors = self.__process_when_steps(when_steps, tickers)
        if not success:
            return False, {}, errors
        # Process Then steps to get final results
        success, then_results, errors = self.__process_then_steps(then_steps, when_results)
        if not success:
            return False, {}, errors
        conditional_tickers = []
        for step in then_steps:
            values = [v['value'] for v in step.get('values', [])]
            if 'list' in step.get('statement'):
                id = values[0]
                # Get tickers where the condition is True
                true_tickers = then_results[then_results[id] == True]['ticker'].tolist()
                conditional_tickers.append({id: true_tickers})

        return True, conditional_tickers, []

if __name__ == "__main__":
    gherkin = """
Feature: v2
Scenario: test
Given stocks from index nifty50
When let ema10Day = latest in 1 samples of day close ema 10
* let close = latest in 1 samples of minute5 close
Then list bulls = tickers with close > ema10Day
"""
    config = os.environ.get("CONFIG_FILE_DEBUG")
    tickers = read_config(config).get('indexes', []).get('nifty50', [])
    indicators = read_config(config).get('indicators', {})
    tz = read_config(config).get('tz', 'Asia/Kolkata')
    data_handler = DataFrameHandler(tz=tz, indicators=indicators)
    data_handler.set_tables(tickers=tickers, interval='1d')
    query_handler = QueryHandler(data_handler)
    print(query_handler.get_gherkin_result(gherkin))

from copy import copy
import logging
import os
import re

from fastapi.params import Query
import numpy
import pandas

# from utility.utility import get_logger
from pytick.dataframe.dataframe import DataFrameHandler
from pytick.dataframe.notification import NotificationHandler
from pytick.query.steps import StepData
from pytick.query.trade import TradeHandler
from pytick.utility.utility import RetVal, get_logger, read_config

logger = get_logger(__file__, logging.DEBUG)


class QueryHandler:
    def __init__(self, data_handler: DataFrameHandler, notification_handler: NotificationHandler, interval_translation: dict, interval_seconds: dict):
        self.data_handler = data_handler
        self.notification_handler = notification_handler
        self.interval_translation = interval_translation
        self.interval_seconds = interval_seconds

    @staticmethod
    def parse_gherkin(gherkin_str: str) -> tuple[bool, dict, list[str]]:
        """
        Validates that the Gherkin string contains only Given, When, Then steps in correct order.
        Returns (True, []) if valid, (False, [error messages]) otherwise.
        """
        lines = [line.strip()
                 for line in gherkin_str.strip().splitlines() if line.strip()]
        errors = []
        if not QueryHandler.__validate_step_order(lines, errors):
            return False, {}, errors
        success, step_data, errors = QueryHandler.__fetch_step_data(lines)
        if not success:
            return False, {}, errors
        return True, step_data, errors

    def get_gherkin_result(self, gherkin_str: str) -> tuple[bool, dict, list, pandas.DataFrame]:
        """ Compute Gherkin result depending on the string, also perform backtest
        queries.
        """
        is_valid, step_data, errors = QueryHandler.parse_gherkin(gherkin_str)
        if not is_valid:
            return False, {}, errors, {}

        given_steps = [
            step for step in step_data if step.get('step') == 'Given']
        when_steps = [step for step in step_data if step.get('step') == 'When']
        then_steps = [step for step in step_data if step.get('step') == 'Then']

        # Process Given steps to get tickers
        success, tickers, g_errors = self.__process_given_steps(given_steps)
        if not success:
            return False, {}, g_errors, pandas.DataFrame()
        # Process When steps to calculate variables
        success, when_results, w_errors = self.__process_when_steps(
            when_steps, tickers)
        if not success:
            return False, {}, w_errors, pandas.DataFrame()
        # Process Then steps to get final results
        success, then_results, t_errors = self.__process_then_steps(
            then_steps, when_results)
        if not success:
            return False, {}, t_errors, pandas.DataFrame()

        conditional_tickers = []
        for step in then_steps:
            values = [v['value'] for v in step.get('values', [])]
            if 'list' in step.get('statement'):
                id = values[0]
                # Get tickers where the condition is True
                true_tickers = then_results[then_results[id]
                                            == True]['ticker'].tolist()
                conditional_tickers.append({id: true_tickers})

        return True, conditional_tickers, [], then_results

    def get_backtest_result(self, query: str, trade_handler: TradeHandler, window: int, stop_loss_percent: float) -> None:
        """ Create a separate copy of the query handler and data handler to perform backtest logic without affecting the main query handler state.
        Get backtest result for a Gherkin query without performing the backtest
        logic. This is useful for getting the calculated variables and tickers
        before the backtest step.
        """
        try:
            query_intervals, base_interval = self.__sync_bt_data(
                query=query, window=window)
            interval = self.interval_translation[base_interval]
            translated_intervals = [self.interval_translation[i]
                                    for i in query_intervals]

            self.data_handler.trim_tables(
                interval=interval, trim_rows=window)
            end_datetime = None
            try:
                end_datetime = self.data_handler.tables[interval]['SBIN'].iloc[-1]['datetime']
            except Exception as e:
                raise e
            for interval in translated_intervals:
                for ticker in self.data_handler.tables[interval].keys():
                    df = self.data_handler.tables[interval][ticker]
                    clipped_df = df[df['datetime'] <= end_datetime]
                    self.data_handler.tables[interval][ticker] = clipped_df
            success, results, errors, df = self.get_gherkin_result(
                gherkin_str=query)
            if not success:
                msg = f"Exception during query backtest: {errors}"
                logger.warning(msg)
                raise Exception(errors)

            for ticker in df['ticker'].tolist():
                if ticker in self.data_handler.tables[interval]:
                    ticker_df = self.data_handler.tables[interval][ticker]
                    if ticker_df.empty:
                        continue
                    price = ticker_df.iloc[-1]['close']
                    time = ticker_df.iloc[-1]['datetime']
                    side = ""
                    for res in results:
                        for key, tickers in res.items():
                            if ticker in tickers:
                                if key in ['buy']:
                                    side = 'buy'
                                    break
                                elif key in ['sell']:
                                    side = 'sell'
                                    break

                    trade_handler.do_trade(
                        ticker=ticker, side=side, price=price, time=time, stop_per=stop_loss_percent)
        except Exception as e:
            raise e

    def __sync_bt_data(self, query: str, window: int) -> tuple[set, str]:
        is_valid, step_data, errors = QueryHandler.parse_gherkin(query)
        if not is_valid:
            raise Exception(errors)
        intervals = set()
        for step in step_data:
            match = next(
                (i for i in StepData.interval if i in step['statement']), None)
            if match:
                intervals.add(match)

        base_interval = StepData.interval[-1]
        for interval in intervals:
            if self.interval_seconds[interval] < self.interval_seconds[base_interval]:
                base_interval = interval
        return intervals, base_interval

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
    def __fetch_step_data(lines: list) -> tuple[bool, list]:
        errors = []
        step_data = StepData()
        step_patterns = {
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
                errors.append(
                    f"Line does not start with a valid step keyword: {line}")
                return False, match_values, errors
            line_step = ' '.join(step_split[1:])
            for regex, step_data in step_patterns[current_step].items():
                match_obj = re.match(regex, line_step)
                if match_obj:
                    variable_indexes = list(step_data.variables.keys())
                    matches = []
                    for i in range(1, len(match_obj.groups()) + 1):
                        value = match_obj.group(i)
                        allowed_values = step_data.variables.get(
                            variable_indexes[i-1], None)
                        if regex == '^stocks from list (.+)$':
                            tickers = value.replace(' ', '').split(',')
                            if not all(i in allowed_values for i in tickers):
                                errors.append(
                                    f"Invalid value '{value}' for variable '{variable_indexes[i-1]}' in line: '{line_unfiltered}'. Allowed values: {allowed_values}")
                                return False, match_values, errors
                        else:
                            if allowed_values and '<' not in allowed_values[0] and '>' not in allowed_values[0]:
                                if value not in allowed_values:
                                    errors.append(
                                        f"Invalid value '{value}' for variable '{variable_indexes[i-1]}' in line: '{line_unfiltered}'. Allowed values: {allowed_values}")
                                    return False, match_values, errors
                        matches.append(
                            {'index': variable_indexes[i-1], 'value': value})
                    match_values.append({'statement': line_unfiltered, 'regex': regex,
                                        'values': matches, 'step': current_step, 'logic': step_data.logic})
                    matched = True
            if not matched:
                errors.append(
                    f"Regex match for \"{line}\" not found in {list(step_patterns[current_step].keys())}")
        return len(errors) == 0, match_values, errors

    def __process_given_steps(self, given_steps: list) -> tuple[bool, list, list]:
        tickers = []
        for step in given_steps:
            values = [v['value'] for v in step.get('values', [])]
            kwargs = {"tickers": values[0]}
            success, tickers, errors = step.get('logic')(**kwargs)
            if not success:
                logger.warning(f"Exception getting tickers: {errors}")
        if tickers is None or len(tickers) == 0:
            logger.warning("No tickers found from Given steps.")
            return False, {}, errors
        return True, tickers, errors

    def __process_when_steps(self, when_steps: list, given_result: list) -> tuple[bool, pandas.DataFrame, list]:
        result = pandas.DataFrame(columns=['ticker'])
        ret_errors = []
        for step in when_steps:
            values = [v['value'] for v in step.get('values', [])]
            logic_name = step['logic'].__qualname__
            kwargs = {}
            if logic_name == 'calculate_indicators':
                id, operator, query_span, interval, ohlc_source, indicator, window = values
                kwargs = {'id': id, 'operator': operator, 'query_span': query_span,
                          'ohlc_source': ohlc_source, 'indicator': indicator, 'window': window}
            elif logic_name == 'calculate_ohlc':
                id, operator, query_span, interval, ohlc_source = values
                kwargs = {'id': id, 'operator': operator,
                          'query_span': query_span, 'ohlc_source': ohlc_source}
            elif logic_name == 'calculate_notification':
                id, operator, query_span, interval, _ = values
                kwargs = {'id': id, 'operator': operator, 'query_span': query_span,
                          'source': None, 'duration': self.interval_seconds.get(interval, 0)}
            else:
                logger.warning(
                    f"Unknown logic function {logic_name} in When step.")
                return False, None, [f"Unknown logic function {logic_name} in When step."]

            # Add column if it doesn't exist
            if id not in result.columns:
                result[id] = numpy.nan if logic_name != 'calculate_notification' else None

            notifications = self.notification_handler.get_corporate_actions_dfs(
                tickers=given_result)
            for ticker in given_result:
                # Add row for ticker if it doesn't exist
                if ticker not in result['ticker'].values:
                    new_row = {'ticker': ticker}
                    result = pandas.concat(
                        [result, pandas.DataFrame([new_row])], ignore_index=True)
                full_df = self.data_handler.get_tables(tickers=[ticker],
                                                       interval=self.interval_translation[interval]).get('data', {}).get(ticker, None)

                df = full_df
                if df is None or df.empty:
                    # logger.warning(
                    #     f"No data found for ticker {ticker} with interval {interval}")
                    continue
                if logic_name == 'calculate_notification':
                    kwargs['source'] = notifications.get(ticker, None)

                success, val, errors = step.get('logic')(df, **kwargs)
                result.loc[result['ticker'] == ticker, id] = val
                if not success:
                    logger.warning(
                        f"Exception calculating variables: {errors} {ticker}")
                    ret_errors.append(errors)
                    # return False, None, errors
                if success and len(errors) > 0:  # some ticker may have issues
                    logger.warning(f"Calculating variables {ticker}: {errors}")
                    ret_errors.append(errors)
        return True, result, ret_errors

    def __process_then_steps(self, then_steps: list, when_results: pandas.DataFrame) -> tuple[bool, pandas.DataFrame, list]:
        result = when_results
        for step in then_steps:
            values = [v['value'] for v in step.get('values', [])]
            id, condition = values
            kwargs = {'id': id, 'condition': condition}
            success, result, errors = step.get('logic')(result, **kwargs)
            if not success:
                logger.warning(f"Exception calculating Then step: {errors}")
                return False, {}, errors

        return True, result, errors


if __name__ == "__main__":
    gherkin = """
Feature: Nifty50 Parabolic Short Analysis with pytick LLM\n\nScenario: Qullamagie Parabolic Short Setup Analysis\n  Given stocks from index nifty50\n  When let close = latest in 1 samples of day close\n  And let sma10 = latest in 1 samples of day close sma 10\n  And let sma20 = latest in 1 samples of day close sma 20\n  And let atr14 = latest in 1 samples of day close atr 14\n  And let prev_close = oldest in 2 samples of day close\n  Then let extension = (close - sma20) / atr14\n  And let sell = [ticker for ticker in list(set(tickers with (extension > 3) & (close < prev_close) & (sma10 > sma20)))]
"""
    config = read_config(os.environ.get("CONFIG_FILE"))
    tickers = config.get('indexes', []).get('nifty50', [])
    indicators = config.get('indicators', {})
    tz = config.get('tz', 'Asia/Kolkata')
    data_handler = DataFrameHandler(tz=tz, indicators=indicators)
    notification_handler = NotificationHandler(
        tz=tz, max_rows=1000, app_data_path=config.get('app_data_path', ''))
    data_handler.set_tables(tickers=tickers, interval='5m')
    notification_handler.set_corporate_actions(tickers=tickers)
    query_handler = QueryHandler(data_handler, notification_handler=notification_handler,
                                 interval_translation={v: k for k, v in config.get(
                                     'interval_translation', {}).items()},
                                 interval_seconds=config.get('interval_seconds', {}))
    # print(query_handler.get_gherkin_result(gherkin, bt_config={'clip': 20, 'forward': 10, 'interval': '5m'}))
    print(query_handler.get_gherkin_result(gherkin))

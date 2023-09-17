import multiprocessing
import time
import re

import pandas

from StockAppApi.processes.python.system.base.system import System, RetVal
from StockAppApi.utility.python.bdd import gherkin_parser
from StockAppApi.processes.python.system.src.steps import given, when, then


class GherkinQuery(System):
    def __init__(self, indicator_config_file: str, selected_stocks_config_file: str, parameter: dict, command_handler: object, name="") -> None:
        """Get the result of gherkin query. Go through all the scenarios and make 
        further queries to the indicators based on the steps then return the result. 
        Note: The Given and Then steps are implemented by this class, whereas the 
        When are implemented by the individual indicators.

        e.g. 
        gherkin --query 
        Feature: Query
        I want to query to get a list of matches
        Scenario: filter for ema and ma 
            Given all nifty 50 stocks
            When ema of window <window> is <condition> <rhs>
            And ma of window <window> is <condition> <rhs>
            Then get list of top 20 stocks

            Examples:
                | window    | condition     | rhs       |
                | 20        | >             | close     |
                | 60        | >             | close     |

        Scenario: check ema
            Given all nifty 50 stocks
            When ema of window 50 is > open
            Then get list of top 10 stocks

        Scenario: check ma
            Given all nifty 50 stocks
            When ma of window 100 is > high
            Then get list of top 10 stocks


        Args:
            indicator_config_file (str): indicator configuration
            selected_stocks_config_file (str): selected stocks list
            parameter (dict): key-value pairs for setting up the query
            name (str, optional): Name of the query. Defaults to "".
        """
        super().__init__(indicator_config_file=indicator_config_file,
                         selected_stocks_config_file=selected_stocks_config_file,
                         parameter=parameter,
                         command_handler=command_handler,
                         name=name)

        self.commands = {
            'get': self.__get,  # call with single ticker
            # 'where': self.__where # call with single ticker
        }

        self.steps = {}

        def add_steps(supported_steps):
            for regex, func in supported_steps.items():
                self.steps[regex] = func
        add_steps(given.get_steps())
        add_steps(when.get_steps())
        add_steps(then.get_steps())

    def __call_if_step_matched(self, rule: str):
        result = {
            'matched': False,
            'match': None,
            'func': None
        }
        for pattern, func in self.steps.items():
            match = re.search(pattern, rule)
            if match:
                result['matched'] = True
                result['match'] = match
                result['func'] = func
                break
        return result

    def __get(self) -> RetVal:
        try:
            check = gherkin_parser.parse(
                gherkin_string=self.parameter['gherkin'])
            conjunction_keyword = ['And ', '* ']
            scenario_results = {}
            for scenario in check["scenarios"]:
                step_results = []
                # populate the given, when, then keywords to make further query
                current_keyword = ""
                for step in check["scenarios"][scenario]:
                    try:
                        errors = ""
                        keyword = step['keyword']
                        step_text = step['text']
                        matched_step = self.__call_if_step_matched(step_text)
                        step_result = {
                            'parent': "",
                            'type': keyword,
                            'step': step_text,
                            'result': "",
                            'errors': ""
                        }
                        if matched_step['matched']:
                            if keyword == 'Given ' or (current_keyword == 'Given ' and keyword in conjunction_keyword):
                                # 1st step -> read the context
                                # e.g. set the interval, selected stock etc.
                                step_result['parent'] = "" if keyword == 'Given ' else 'given'
                                step_result['result'] = matched_step['func'](
                                    self.selected_stocks_config_file, self.indicator_config_file, matched_step["match"].groups())
                                current_keyword = 'Given '
                                step_results.append(step_result)
                            elif keyword == 'When ' or (current_keyword == 'When ' and keyword in conjunction_keyword):
                                # 2nd step -> compute the condition
                                # get the context from given above and generate result
                                # based on the condition
                                def execute_when(errors: str):
                                    errors = ""
                                    valid_tickers = []
                                    given_tickers = []
                                    for rslt in step_results:
                                        if rslt['type'] == "Given " or rslt["parent"] == "given":
                                            for tick in rslt['result']['tickers']:
                                                if tick not in given_tickers:
                                                    given_tickers.append(tick)

                                    args = []
                                    for ticker in given_tickers:
                                        args.append(
                                            (self.selected_stocks_config_file, self.indicator_config_file, ticker, matched_step["match"].groups()))

                                    multi_results = None
                                    with multiprocessing.Pool() as pool:
                                        try:
                                            multi_results = pool.starmap(
                                                matched_step["func"], args)
                                        except Exception as e:
                                            errors += f"{e.args}"

                                    for result in multi_results:
                                        satisfies = False
                                        if isinstance(result["condition"], bool):
                                            satisfies = result["condition"]
                                        if isinstance(result["condition"], list):
                                            satisfies = any(result["condition"])
                                            
                                        if result["exception"] is None:
                                            if satisfies :
                                                valid_tickers.append(result)
                                        else:
                                            errors += f'{result["ticker"]} -> {result["exception"]} \n'
                                    valid_tickers.sort(
                                        key=lambda stock: stock['ticker'])
                                    return valid_tickers, errors

                                step_result['parent'] = "" if keyword == 'When ' else 'when'
                                step_result['result'], step_result['errors'] = execute_when(
                                    errors=errors)
                                current_keyword = 'When '
                                step_results.append(step_result)
                            elif keyword == 'Then ' or (current_keyword == 'Then ' and keyword in conjunction_keyword):
                                # 3rd step -> data presentation
                                step_result['parent'] = "" if keyword == 'Then ' else 'then'
                                step_result['result'] = matched_step['func'](
                                    matched_step["match"].groups(), step_results)
                                current_keyword = 'Then '
                                step_results.append(step_result)
                            else:
                                raise Exception(
                                    f'Exception in matching keyword {keyword}')
                        else:
                            raise Exception(f'No matching steps found {step}')
                    except Exception as e:
                        errors += f"{step}->{e.args}\n"
                        step_result['errors'] = errors
                        raise Exception(errors)
                scenario_results[scenario] = step_results
            return RetVal(obj={check['feature']: scenario_results},
                          obj_as_str="a dict of when given then result")
        except Exception as e:
            return RetVal(obj=None, obj_as_str="ERROR", errors=f"{self.parameter['ticker']}->{e.args}")


if __name__ == "__main__":
    from StockAppApi.processes.python.system.src.command_handler import CommandHandler
    g_query = '''
Feature: test
I want to query to get a list of turtle S1 stocks      
Scenario: test
Given nifty50 stocks
When day close > high of last 20 ticks
Then get list of all match
    '''
    start = time.time()
    configFolder = "StockAppApi/configuration/"
    indicator_config_yaml = configFolder + "indicator.yaml"
    selected_stocks_yaml = configFolder + "selected_stocks.yaml"
    commandHandler = CommandHandler(
        selected_stocks_yaml, indicator_config_yaml=indicator_config_yaml)
    parser = GherkinQuery(indicator_config_file=indicator_config_yaml,
                          selected_stocks_config_file=selected_stocks_yaml,
                          command_handler=commandHandler,
                          parameter={'do': 'get', 'gherkin': g_query},
                          name="")

    check = parser.execute()
    print(check.obj["test"])
    print("elasped time", time.time() - start)

'''
Feature: Back test day turtle S1
    I want to query to backtest in stocks
    Scenario: backtest stocks
    Given nifty 100 stocks
    When backtest for last 100 ticks with signal color green | day close > close of last 55 ticks
    Then get list of stocks with signals
    Feature: Back test
    I want to query to backtest in stocks
    Scenario: backtest stocks
    Given nifty 50 stocks
    When backtest for last 100 ticks with signal color green | day close shows macd divergence with window 20 fastperiod 12 slowperiod 26 signalperiod 9 in last 40 ticks
    Then get list of stocks with signals
Feature: Stocks with MACD divergence
    I want to query to get a list of macd divergence stocks      
    Scenario: list stocks showing macd divergence
    Given nifty 50 stocks
    When day close shows macd divergence with window 20 in last 40 ticks
    Then get list of stocks with signals
    Feature: Query
    I want to query to get a list of matches      
        Scenario: filter for ema and ma 
        Given nifty 50 stocks
        When <interval> <ohlc source> <indicator> <window> <condition> <ohlc>
        And hour close ma 100 < hour open ma 20
        Then get list of top 20

        Examples:
        | interval  | ohlc source       | indicator     | window    | condition     | ohlc      |   
        | day       | close             | ema           | 20        | >             | open      |
        | week      | open              | ma            | 60        | >             | close     | 
        
        Scenario: check ema50
        Given nifty 100 stocks
        When week close ema 50 > open
        Then get list of top 10
        
        Scenario: check ema70
        Given nifty 200 stocks
        When week close ema 70 > day open ma 20
        Then get list of top 10
    '''
'''
    g_query = 
    Feature: Query
    I want to query to get a list of matches      
        Scenario: filter for ema and ma 
        Given nifty 50 stocks
        When <interval> <ohlc source> <indicator> <window> <condition> <ohlc>
        And hour close ma 100 < hour open ma 20
        Then get list of top 20

        Examples:
        | interval  | ohlc source       | indicator     | window    | condition     | ohlc      |   
        | day       | close             | ema           | 20        | >             | open      |
        | week      | open              | ma            | 60        | >             | close     | 
        
        Scenario: check ema50
        Given nifty 100 stocks
        When week close ema 50 > open
        Then get list of top 10
        
        Scenario: check ema70
        Given nifty 200 stocks
        When week close ema 70 > close
        Then get list of top 10

    '''

import json
import pandas
import re
import numpy
from scipy.stats import linregress

from StockAppApi.processes.python.system.base.system import System, RetVal
from StockAppApi.processes.python.talib.src.ema import Ema
from StockAppApi.processes.python.talib.src.macd import Macd
from StockAppApi.processes.python.talib.src.rsi import Rsi
from StockAppApi.processes.python.talib.src.rsi_line import RsiLine
from StockAppApi.processes.python.talib.src.ma import Ma
from StockAppApi.processes.python.talib.base.indicator import Indicator
from StockAppApi.base.python.src.yaml_parser import read_config
from StockAppApi.utility.python.bdd import gherkin_parser
from StockAppApi.utility.python.bdd.steps import given, then, when


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
        self.indicators = {
            'ema': Ema,
            'macd': Macd,
            'macdhist': Macd,
            'macdsignal': Macd,
            'rsi': Rsi,
            'rsiline': RsiLine,
            'ma': Ma
        }

        self.commands = {
            'get': self.__get,  # call with single ticker
            # 'where': self.__where # call with single ticker
        }

        self.steps = {
            # nifty 50 stocks
            r'^(\w+)\s+(\d+)\s+stocks$': self.__get_selected_stocks,
            # get list of all match
            r'^get list of (\w+) match$': self.__get_list,
            # day close ema 50 > close
            r'^(\w+)\s+(\w+)\s+(\w+)\s+(\d+)\s+([><=!]+)\s+(\w+)$': self.__indicator_compare_with_ohlc,
            # day close ema 50 > day close ma 20
            r'^(\w+)\s+(\w+)\s+(\w+)\s+(\d+)\s+([><=!]+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\d+)$': self.__indicator_compare_indicator,
            # day close ma 50 in uptrend for 90 days
            r'^(\w+) (\w+) (\w+) (\d+) in (\w+) for (\d+) days$': self.__indicator_slope_compare_value,
            # 1.25 of 52 week low < close
            r'^([-+]?\d*\.\d+) of (\d+) (\w+) (\w+) ([><=!]+) (\w+)$': self.__ohlc_compare_value,
        }
    
    @given
    def __get_selected_stocks(self, **kwargs):
        # TODO logic to select selected stocks
        match = kwargs["match"]
        index = match.group(1)
        return {
            # TODO set tickers based on selected index
            'tickers': self._get_indices() + self._get_tickers()
        }

    @when
    def __indicator_compare_with_ohlc(self, **kwargs) -> dict:
        match = kwargs["match"]
        interval, ohlc_source_ind_lsh, ind_lhs, ind_lhs_window, condition, \
            ohlc_rhs  = match.groups()
        indicator_query = f'talibquery --ticker {kwargs["ticker"]} \
            --interval {interval} --do get --csv 0 \
            --indicator {ind_lhs} --window {ind_lhs_window} --n 1000 \
            --ohlc {ohlc_source_ind_lsh.capitalize()} --latest {self.parameter["latest"]}'
        df = self.command_handler.execute(indicator_query, is_rest=False).obj
        df.columns = df.columns.str.lower()
        condition_string = f'{df[ind_lhs].iloc[-1]} {condition} {df[ohlc_rhs].iloc[-1]}'
        return {
            "condition": eval(condition_string)
        }
    
    @when
    def __indicator_compare_indicator(self, **kwargs):
        match = kwargs["match"]
        interval_lhs, ohlc_source_ind_lsh, ind_lhs, ind_lhs_window, condition, \
            interval_rhs, ohlc_source_ind_rsh, ind_rhs, ind_rhs_window  = match.groups()

        ind_lhs_query = f'talibquery --ticker {kwargs["ticker"]} \
            --interval {interval_lhs} --do get --csv 0 \
            --indicator {ind_lhs} --window {ind_lhs_window} --n 1000 \
            --ohlc {ohlc_source_ind_lsh.capitalize()} --latest {self.parameter["latest"]}'
        ind_rhs_query = f'talibquery --ticker {kwargs["ticker"]} \
            --interval {interval_rhs} --do get --csv 0 \
            --indicator {ind_rhs} --window {ind_rhs_window} --n 1000 \
            --ohlc {ohlc_source_ind_rsh.capitalize()} --latest {self.parameter["latest"]}'
        df_lhs = self.command_handler.execute(ind_lhs_query, is_rest=False).obj[ind_lhs]
        df_rhs = self.command_handler.execute(ind_rhs_query, is_rest=False).obj[ind_rhs]
        condition_string = f'{df_lhs.iloc[-1]} {condition} {df_rhs.iloc[-1]}'
        return {
            "condition": eval(condition_string)
        }
        
    @when
    def __indicator_slope_compare_value(self, **kwargs):
        # day close ma 50 in uptrend for 90 days
        match = kwargs["match"]
        interval, ohlc_source_ind_lsh, ind_lhs, ind_lhs_window, trend, \
            days_span  = match.groups()
        indicator_query = f'talibquery --ticker {kwargs["ticker"]} \
            --interval {interval} --do get --csv 0 \
            --indicator {ind_lhs} --window {ind_lhs_window} --n 1000 \
            --ohlc {ohlc_source_ind_lsh.capitalize()} --latest {self.parameter["latest"]}'
        df = self.command_handler.execute(indicator_query, is_rest=False).obj[ind_lhs]
        df = df.tail(int(days_span))
        slope, _, _, _, _ = linregress(
                        numpy.arange(0, df.shape[0], 1), df)
        condition = '>' if trend == 'uptrend' else '<'
        condition_string = f'{slope} {condition} 0'
        return {
            "condition": eval(condition_string)
        }
    
    @when
    def __ohlc_compare_value(self, **kwargs):
        match = kwargs["match"]
        mulitplier, window, interval, ohlc_lhs, condition, ohlc_rhs  = match.groups()
        ticker_ohlc_csv_path = f'{self.indicator_config["indicator"]["data"][interval]}/{kwargs["ticker"]}.csv'
        df = pandas.read_csv(ticker_ohlc_csv_path)
                
        # lhs ohlc  
        lhs = (df[ohlc_lhs.capitalize()].tail(int(window)).min()) * float(mulitplier)
        condition_string = f'{lhs} {condition} {df[ohlc_rhs.capitalize()].iloc[-1]}'
        return {
            "condition": eval(condition_string)
        }
        
    @then
    def __get_list(self, **kwargs):
        selection = '&' if kwargs["match"].group(1) == 'all' else '+'
        ret = []
        for step in kwargs["steps"]:
            if step['type'] == "When " or step["parent"] == "when":
                if len(ret) == 0:
                    ret = step['result']
                else: 
                    if kwargs["match"].group(1) == 'all':
                        ret = list(set(ret) & set(step['result']))
                    elif kwargs["match"].group(1) == 'any':
                        ret = list(set(ret + step['result']))
                    else:
                        raise Exception("Not valid selection")
            
        return {
            "selection": selection,
            "tickers": ret
        }

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
            check = gherkin_parser.parse(gherkin_string=self.parameter['gherkin'])
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
                                step_result['result'] = matched_step['func'](match=matched_step["match"])
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
                                                
                                    for ticker in given_tickers:
                                        try:
                                            ret = matched_step['func'](match=matched_step["match"], ticker=ticker)
                                            if ret['condition']:
                                                valid_tickers.append(ticker)
                                        except Exception as e:
                                            errors += f"{ticker}->{e.args}\n"
                                            continue
                                    return valid_tickers, errors
                                
                                step_result['parent'] = "" if keyword == 'When ' else 'when'
                                step_result['result'], step_result['errors'] = execute_when(errors=errors)
                                current_keyword = 'When '
                                step_results.append(step_result)
                            elif keyword == 'Then ' or (current_keyword == 'Then ' and keyword in conjunction_keyword):
                            # 3rd step -> data presentation
                                step_result['parent'] = "" if keyword == 'Then ' else 'then'
                                step_result['result'] = matched_step['func'](match=matched_step["match"], steps=step_results)
                                current_keyword = 'Then '
                                step_results.append(step_result)
                            else:
                                raise Exception(f'Exception in matching keyword {keyword}')
                        else:
                            raise Exception(f'No matching steps found {step}')
                    except Exception as e:
                        errors += f"{step}->{e.args}\n"
                        step_result['errors'] = errors
                        raise Exception(errors)
                scenario_results[scenario] = step_results
            return RetVal(obj=scenario_results,
                          obj_as_str="a dict of when given then result")
        except Exception as e:
            return RetVal(obj=None, obj_as_str="ERROR", errors=f"{self.parameter['ticker']}->{e.args}")
        
        
if __name__ == "__main__":
    from StockAppApi.processes.python.system.src.command_handler import CommandHandler
    g_query = '''
    Feature: Query
    I want to query to get a list of matches      
    Scenario: list stocks in stage 2 uptrend
    Given nifty 50 stocks
    When day close ma 150 < close
    * day close ma 200 < close
    * day close ma 150 > day close ma 200
    * day close ma 50 in uptrend for 90 days
    * 1.25 of 52 week low < close
    * 0.75 of 52 week high < close
    * day close ma 50 < close
    Then get list of all match
    '''
    configFolder = "StockAppApi/configuration/"
    indicator_config_yaml = configFolder + "indicator.yaml"   
    selected_stocks_yaml = configFolder + "selected_stocks.yaml"
    commandHandler = CommandHandler(selected_stocks_yaml, indicator_config_yaml=indicator_config_yaml)
    parser = GherkinQuery(indicator_config_file=indicator_config_yaml, 
                      selected_stocks_config_file=selected_stocks_yaml,
                      command_handler=commandHandler,
                      parameter={'do':'get', 'gherkin': g_query},
                      name="")
        
    check = parser.execute()
    print(json.loads(check.obj))              

'''
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

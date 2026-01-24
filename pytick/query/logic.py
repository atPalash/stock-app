import logging
import os
import re

from dotenv import load_dotenv
import numpy
import pandas
from pytick import dataframe
from pytick.utility.utility import get_logger, read_config
from pytick.dataframe.dataframe import calculate_indicators

load_dotenv()

config = os.environ.get("CONFIG_FILE")
logger = get_logger(__name__, logging.DEBUG)

def get_index_tickers(**kwargs) -> tuple:
    """Get a list of stocks for the selected index.

    Args:
        index (str): The index for which to retrieve tickers.

    Returns:
        tuple: success flag, tickers list, errors list.
    """
    errors = []
    index = kwargs.get('tickers', None)
    tickers = read_config(config).get('indexes', {}).get(index, [])
    if not tickers:
        errors.append(f"Index '{index}' not found. Available indexes: {list(read_config(config).get('indexes', {}).keys())}")
        return False, None, errors
    return True, tickers, errors

def get_stocks(**kwargs) -> tuple:
    """Convert csv tickers to a list.

    Args:
        groups (tuple): tickers as csv string.

    Returns:
        tuple: success flag, tickers list, errors list.
    """
    errors = []
    tickers_str = kwargs.get('tickers', '')
    tickers = [ticker.strip() for ticker in tickers_str.split(",") if ticker.strip()]
    if not tickers:
        errors.append("No valid tickers found.")
        return False, [], errors
    return True, tickers, errors

def calculate_indicators(
   df, **kwargs
) -> tuple:
    errors= []
    try:
        indicator_key = f"{kwargs['indicator']}_{kwargs['window']}_{kwargs['ohlc_source']}"
        data = df[indicator_key].dropna().to_numpy()
        if data.size == 0:
            errors.append(f"No data available for indicator {indicator_key}")
            return True, numpy.nan, errors
        return True, __eval_operator(kwargs['operator'], kwargs['query_span'], data), errors
    except Exception as e:
        errors.append(f"Exception calculating variable {kwargs['id']}: {e}, check supported indicator settings")
        return False, numpy.nan, errors

def calculate_ohlc(
    df, **kwargs
) -> tuple:
    errors= []
    try:
        indicator_key = f"{kwargs['ohlc_source']}"
        data = df[indicator_key].dropna().to_numpy()
        if data.size == 0:
            errors.append(f"No data available for indicator {indicator_key}")
            return True, numpy.nan, errors
        return True, __eval_operator(kwargs['operator'], kwargs['query_span'], data), errors
    except Exception as e:
        errors.append(f"Exception calculating variable {kwargs['id']}: {e}, check supported ohlc settings")
        return False, numpy.nan, errors

def calculate_conditions(when_results: pandas.DataFrame, **kwargs) -> tuple:
    errors = []
    result = when_results.copy()
    id, condition = kwargs.get('id'), kwargs.get('condition')
    
    try:
        # Parse and evaluate condition for all rows
        condition = to_bitwise(condition)
        result[id] = result.eval(condition)
        return True, result, errors
    except Exception as e:
        errors.append(f"Exception evaluating condition '{condition}': {e}")
        return False, False, errors
        
def __eval_operator(operator, span: str, data: numpy.array):
    try:
        span_window = int(span)
        data_for_span = data[-span_window:]
        result = numpy.nan
        if operator == "latest":
            result = data_for_span[-1]
        elif operator == "oldest":
            result = data_for_span[0]
        elif operator == "minimum":
            result = numpy.min(data_for_span)
        elif operator == "maximum":
            result = numpy.max(data_for_span)
        elif operator == "average":
            result = round(numpy.mean(data_for_span), 2)
        elif operator == "rate":
            result = round((data_for_span[-1] - data_for_span[0]) / span_window, 2)
        elif operator == "change":
            result = round((data_for_span[-1] - data_for_span[0]) / data[0], 2)
        else:
            raise Exception(f"Unsupported operator: {operator}")
        return round(float(result), 2)
    except Exception as e:
        raise Exception(f"Exception in operator {operator} {e.args}")

def to_bitwise(expr:str) -> str:
    """Convert logical operators in expression to bitwise operators.

    Args:
        expr (str): The expression string.
    """
    expr = re.sub(r'\bnot\b', '~', expr)
    expr = re.sub(r'\band\b', '&', expr)
    expr = re.sub(r'\bor\b',  '|', expr)
    return expr   
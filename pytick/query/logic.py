import logging
import os

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
        return False, None, errors
    return True, tickers, errors

def calculate_indicators(
   df, **kwargs
) -> tuple:
    errors= []
    try:
        indicator_key = f"{kwargs['indicator']}_{kwargs['window']}_{kwargs['ohlc_source']}"
        data = df[indicator_key].dropna().to_numpy()
        return True, __eval_operator(kwargs['operator'], kwargs['query_span'], data), errors
    except Exception as e:
        errors.append(f"Error calculating variable {kwargs['id']}: {e}")
        return False, None, errors

def calculate_ohlc(
    df, **kwargs
) -> tuple:
    errors= []
    try:
        indicator_key = f"{kwargs['ohlc_source']}"
        data = df[indicator_key].dropna().to_numpy()
        return True, __eval_operator(kwargs['operator'], kwargs['query_span'], data), errors
    except Exception as e:
        errors.append(f"Error calculating variable {kwargs['id']}: {e}")
        return False, None, errors

def calculate_conditions(when_results: pandas.DataFrame, **kwargs) -> tuple:
    errors = []
    result = when_results.copy()
    id, condition = kwargs.get('id'), kwargs.get('condition')
    
    try:
        # Parse and evaluate condition for all rows
        result[id] = eval(condition, None, result.to_dict(orient='series'))
        return True, result, errors
    except Exception as e:
        errors.append(f"Error evaluating condition '{condition}': {e}")
        return False, None, errors

        
def __eval_operator(operator, span: str, data: numpy.array):
    try:
        span_window = int(span)
        data_for_span = data[-span_window:]
        result = None
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
        raise Exception(f"Error in operator {operator} {e.args}")

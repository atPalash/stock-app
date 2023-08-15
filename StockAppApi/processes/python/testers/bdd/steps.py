import functools
import re

def __base_decorator(_func):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            ret = func(*args, **kwargs)
            return ret
        return wrapper
    if _func is None:
        return decorator
    else:
        return decorator(_func)


def given(func):
    return __base_decorator(func)


def when(func):
    return __base_decorator(func)


def then(func):
    return __base_decorator(func)


@when
def indicator_condition(**kwargs):
    match = kwargs["match"]
    return f'--indicator {match.group(1)} --window {match.group(2)} --condition {match.group(3)} --rhs {match.group(4)}'

@given
def select_stocks(**kwargs):
    match = kwargs["match"]
    return f'--index {match.group(1)} {match.group(2)}'

@then
def get_list(**kwargs):
    match = kwargs["match"]
    return f'--list of {match.group(1)} stocks'

pattern_and_method = {
    r'(\w+) of window (\d+\.?\d*) is ([><=!]+) (\w+)': indicator_condition,
    r'all (\w+) (\d+) stocks': select_stocks,
    r'get list of top (\d+) stocks': get_list,
}


def call_matched(rule):
    result = {
        'matched': False,
        'data': None
    }
    for pattern, method in pattern_and_method.items():
        match = re.search(pattern, rule)
        if match:
            result['matched'] = True
            result['data'] = method(match=match)
            break
    return result

# print(call_matched(rule='ema of window 20 is == close'))
# print(call_matched(rule='all nifty 50 stocks'))
# print(call_matched(rule='get list of top 50 stocks'))

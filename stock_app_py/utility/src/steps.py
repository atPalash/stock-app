import functools
import re

def __base_decorator(_func):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                ret = func(*args, **kwargs)
                return ret
            except Exception as e:
                raise
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

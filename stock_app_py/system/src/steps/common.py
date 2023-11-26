import re


def call_if_step_matched(rule: str, steps: dict):
    result = {"matched": False, "match": None, "func": None}
    for pattern, func in steps.items():
        match = re.search(pattern, rule)
        if match:
            result["matched"] = True
            result["match"] = match
            result["func"] = func
            break
    return result

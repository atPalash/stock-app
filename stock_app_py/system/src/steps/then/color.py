from stock_app_py.utility.src.steps import then


@then
def color_tickers(selector, steps):
    try:
        return {"selection": selector, "tickers": []}
    except Exception as e:
        return {"selection": selector, "exception": e.args}

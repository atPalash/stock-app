from stock_app_py.utility.src.steps import when
from stock_app_py.system.src.steps.when import aggregator
import stock_app_py.system.src.command_handler as executor
from stock_app_py.utility.src import date_helper

import pandas
import numpy
import datetime


@when
def quaterly_eps_growth(
    selected_stocks_yaml,
    indicator_config_yaml,
    ticker,
    groups,
    lookback_window: int = -1,
):
    """Query eps growth with different type
    * net - slope of eps growth
    * recent - growth compared to last quarter
    * quarter to quarter - growth comparted to same quarter last year

    Args:
        selected_stocks_yaml (str): selected stocks list
        indicator_config_yaml (str): indicator config
        ticker (str): ticker name e.g ABB
        groups (regex groups): read the user input value from this
        lookback_window (int, optional): used for backtest as the window to look back and compute the logic

    Returns:
        dict: dictionary containing the result of the logic
    """
    try:
        condition_type = "quarter to quarter"
        if len(groups) == 3:
            condition_type, condition, threshold = groups
        elif len(groups) == 2:
            condition, threshold = groups
        else:
            raise Exception(f"Gherkin query arguments should be 2 or 3 : {groups}")

        command_handler = executor.CommandHandler(
            selected_stocks_yaml, indicator_config_yaml
        )
        financials_query = f"yahoofinance --ticker {ticker} --do financials"
        financials = command_handler.execute(financials_query, is_rest=False).obj
        ohlc_query = f"yahoofinance --ticker {ticker} --interval week --do ohlc"
        ohlc = command_handler.execute(ohlc_query, is_rest=False).obj

        eps = []
        quarters = []
        for quarter, statement in financials["incomeStatementHistoryQuarterly"].items():
            if "basicEPS" in statement:
                eps.append(statement["basicEPS"])
                quarters.append(quarter)

        def net(date):
            try:
                _, index = date_helper.find_closest_date(date, quarters)
                index = index + 1  # include this index also
                start_date = quarters[0]
                quarter_series = [(x - start_date).days for x in quarters[:index]]
                slope, _ = numpy.polyfit(quarter_series, eps[:index], 1)
                return slope
            except Exception as e:
                raise

        def previous_to_quarter(date):
            try:
                _, index = date_helper.find_closest_date(date, quarters)
                index = index + 1  # include this index also
                selected_eps = eps[:index]
                growth_rates = {quarters[0]: 0}
                for i in range(0, len(selected_eps) - 1):
                    beginning_value = selected_eps[i]
                    ending_value = selected_eps[i + 1]
                    growth_rate = round(
                        (ending_value - beginning_value) / beginning_value, 2
                    )
                    growth_rates[quarters[i + 1]] = growth_rate
                return growth_rates[quarters[-1]]
            except Exception as e:
                raise

        def quarter_to_quarter(date):
            try:
                _, index = date_helper.find_closest_date(date, quarters)
                index = index + 1  # include this index also
                selected_eps = eps[:index]
                selected_quarters = quarters[:index]
                this_quarter = selected_quarters[-1]
                previous_year_quarter = this_quarter - datetime.timedelta(days=365)
                previous_year_quarter, index = date_helper.find_closest_date(
                    previous_year_quarter, quarters
                )

                this_quarter_eps = selected_eps[-1]
                previous_year_quarter_eps = selected_eps[index]
                return round(
                    (this_quarter_eps - previous_year_quarter_eps)
                    / previous_year_quarter_eps,
                    2,
                )
            except Exception as e:
                raise

        condition_funcs = {
            "net": net,
            "recent": previous_to_quarter,
            "quarter to quarter": quarter_to_quarter,
        }

        def logic(df: pandas.DataFrame):
            try:
                df_last_date = datetime.datetime.strptime(
                    df.iloc[-1]["Date"], "%Y-%m-%d"
                )
                query_quarter, _ = date_helper.find_closest_date(df_last_date, quarters)
                rate = condition_funcs[condition_type](df_last_date)
                condition_string = f"{rate} {condition} {float(threshold) / 100}"
                return {
                    "ticker": ticker,
                    "query": "quaterly_eps_growth",
                    "interval": "week",
                    "quarter": query_quarter,
                    "condition": eval(condition_string),
                    "exception": None,
                }
            except Exception as e:
                raise

        return aggregator.get_result(
            lookback_window=lookback_window, logic=logic, ticker_df=ohlc
        )
    except Exception as e:
        return {"ticker": ticker, "exception": e.args}

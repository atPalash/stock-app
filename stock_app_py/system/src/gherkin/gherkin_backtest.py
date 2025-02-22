import random
from flask import jsonify
import numpy as np
import pandas
import nsepython

from stock_app_py.system.src.gherkin.gherkin_backtest_ohlc_helper import (
    GherkinBacktestOhlcHelper,
)
from stock_app_py.system.src.gherkin.gherkin_generic_query import GherkinGenericQuery
from stock_app_py.system.src.options.chain import OptionChain
from stock_app_py.system.src.options.strategy.iron_condor import IronCondor
from stock_app_py.system.src.options.strategy.spread import Spread
from stock_app_py.system.src.yahoo_finance import YahooFinance
from stock_app_py.utility.src.path_helper import get_app_path
from stock_app_py.utility.src import date_helper
from stock_app_py.utility.src.logger import get_logger
from stock_app_py.system.base.system import System
from stock_app_py.system.interface.system_if import RetVal
from stock_app_py.system.src.options import price

logger = get_logger(__name__)

SCENARIO = "backtest"


class GherkinBacktest(System):
    def __init__(
        self,
        indicator_config_file: str,
        selected_stocks_config_file: str,
        parameter: dict,
        command_handler: object,
        name="",
    ) -> None:

        super().__init__(
            indicator_config_file=indicator_config_file,
            selected_stocks_config_file=selected_stocks_config_file,
            parameter=parameter,
            command_handler=command_handler,
            name=name,
        )

        self.commands = {"get": self.__get}

    def __get(self) -> RetVal:
        result = [None, ""]
        try:
            test_count = self.parameter["n"]
            test_window = self.parameter["window"]
            test_interval = self.parameter["interval"]
            gherkin_query = self.parameter["gherkin"]
            net_pos_predictions = 0
            net_neg_predictions = 0
            for i in range(test_count):
                look_back = random.randint(test_window, 1000)
                if i == 0:
                    look_back = test_window

                backtest_ohlc_helper = GherkinBacktestOhlcHelper(
                    indicator_config_file=self.indicator_config_file,
                    selected_stocks_config_file=self.selected_stocks_config_file,
                    command_handler=None,
                    parameter={
                        "interval": test_interval,
                        "lookback": look_back,
                    },
                    name="",
                )
                gherkin_gen_query = GherkinGenericQuery(
                    indicator_config_file=self.indicator_config_file,
                    selected_stocks_config_file=self.selected_stocks_config_file,
                    command_handler=None,
                    parameter={"gherkin": gherkin_query},
                    gherkin_ohlc_helper=backtest_ohlc_helper,
                    name="",
                )
                gherkin_result = gherkin_gen_query.execute().obj
                query_df = gherkin_result[SCENARIO]["query_df"]

                ohlc_on_both_window_end = (
                    backtest_ohlc_helper.get_ohlc_on_both_window_end(
                        tickers=gherkin_gen_query.get_tickers(), window=test_window
                    )
                )
                for index, row in query_df.iterrows():
                    ticker = row["ticker"]

                    ticker_both_end = ohlc_on_both_window_end[ticker]
                    start_date = ticker_both_end["start"]["Datetime"]
                    end_date = ticker_both_end["end"]["Datetime"]
                    start_close = ticker_both_end["start"]["Close"]
                    end_close = ticker_both_end["end"]["Close"]
                    action = "bull" if end_close > start_close else "bear"
                    prediction = (
                        int(
                            (action == "bull" and row["bull"])
                            or (action == "bear" and row["bear"])
                        )
                        if row["bull"] != row["bear"]
                        else -1
                    )

                    to_add = {
                        "start_date": start_date,
                        "start_close": start_close,
                        "end_date": end_date,
                        "end_close": end_close,
                        "action": action,
                        "prediction": prediction,
                    }

                    for k, v in to_add.items():
                        query_df.at[index, k] = v

                pos_prediction_count = (query_df["prediction"] == 1).sum()
                neg_prediction_count = (query_df["prediction"] == 0).sum()
                total_count = pos_prediction_count + neg_prediction_count
                net_pos_predictions += pos_prediction_count
                net_neg_predictions += neg_prediction_count
                # print(query_df)
                # print(
                #     f"start {start_date} end {end_date}\nFailure % {round(neg_prediction_count * 100/ total_count)}\nSuccess % {round(pos_prediction_count * 100/ total_count)}"
                # )
            net_predictions = net_pos_predictions + net_neg_predictions
            print(
                f"window {test_window} positive {round(net_pos_predictions * 100/net_predictions)}% negative {round(net_neg_predictions * 100/net_predictions)}%"
            )

        except Exception as e:
            logger.error(e)
        return RetVal(
            obj=result[0], obj_as_str="probable option price", errors=result[1]
        )

    def debug(self):
        return self.__get()


if __name__ == "__main__":
    indicator_config_yaml = get_app_path("indicator.yaml")
    selected_stocks_yaml = get_app_path("selected_stocks.yaml")
    gherkin = f"""Feature: v2\n
    Scenario: {SCENARIO}\n
    Given stocks from index nifty50\n
    When let ema10Change = rate in 20 samples of minute5 close ema 10\n
    * let vwap10Change = rate in 20 samples of minute5 close vwap 10\n
    * let ema10Day = latest in 1 samples of day close ema 10\n
    * let close = latest in 1 samples of minute5 close\n
    Then let inrange = close > ema10Day * 0.99 and close < ema10Day * 1.01\n
    * list bull = tickers with ema10Change > 0 and vwap10Change > 0 and inrange\n
    * list bear = tickers with ema10Change < 0 and vwap10Change < 0 and inrange\n
    """
    for window in range(10, 100, 10):
        ut = GherkinBacktest(
            indicator_config_file=indicator_config_yaml,
            selected_stocks_config_file=selected_stocks_yaml,
            command_handler=None,
            parameter={
                "window": window,
                "interval": "minute5",
                "n": 5,
                "gherkin": gherkin,
            },
            name="",
        )
        ut.debug()

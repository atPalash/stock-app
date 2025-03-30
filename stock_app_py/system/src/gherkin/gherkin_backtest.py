import random
import pandas

from stock_app_py.system.src.gherkin.gherkin_backtest_ohlc_helper import (
    GherkinBacktestOhlcHelper,
)
from stock_app_py.system.src.gherkin.gherkin_generic_query import GherkinGenericQuery
from stock_app_py.system.src.gherkin.gherkin_helper import merge_gherkin_list
from stock_app_py.utility.src import gherkin_parser
from stock_app_py.utility.src.path_helper import get_app_path
from stock_app_py.utility.src.logger import get_logger
from stock_app_py.system.base.system import System
from stock_app_py.system.interface.system_if import RetVal

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
        self.gherkins = self.parameter["TEST"]

    def __get(self) -> RetVal:
        result = [None, ""]
        try:
            test_count = self.parameter["n"]
            test_window = self.parameter["window"]
            test_interval = self.parameter["interval"]
            gherkin_query = self.parameter["gherkin"]
            net_pos_predictions = 0
            net_neg_predictions = 0
            net_gain_percentage = 0
            test_result = []
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
                gherkin_query = merge_gherkin_list(
                    gherkins=self.gherkins, scenario=SCENARIO
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
                    query_df.at[index, "start_date"] = start_date
                    query_df.at[index, "end_date"] = end_date
                    query_df.at[index, "start_close"] = start_close
                    query_df.at[index, "end_close"] = end_close
                    query_df.at[index, "action"] = action

                    for gid in self.gherkins.keys():
                        prediction_key = f"prediction_{gid}"
                        query_df.at[index, prediction_key] = (
                            "none"  # start with no prediction
                        )
                        query_df.at[index, f"gain%_{prediction_key}"] = 0
                        if row[f"bull_{gid}"] != row[f"bear_{gid}"]:
                            # We make a directional prediction
                            if action == "bull":
                                delta = round(
                                    (end_close - start_close) * 100 / start_close, 2
                                )
                                if row[f"bull_{gid}"]:
                                    query_df.at[index, prediction_key] = "right"
                                    query_df.at[index, f"gain%_{prediction_key}"] = (
                                        delta
                                    )
                                else:
                                    query_df.at[index, prediction_key] = "wrong"
                                    query_df.at[index, f"gain%_{prediction_key}"] = (
                                        -delta
                                    )
                            elif action == "bear":
                                delta = round(
                                    (start_close - end_close) * 100 / start_close, 2
                                )
                                if row[f"bear_{gid}"]:
                                    query_df.at[index, prediction_key] = "right"
                                    query_df.at[index, f"gain%_{prediction_key}"] = (
                                        delta
                                    )
                                else:
                                    query_df.at[index, prediction_key] = "wrong"
                                    query_df.at[index, f"gain%_{prediction_key}"] = (
                                        -delta
                                    )
                            else:
                                logger.error("This should not happen")
                test_result.append(query_df)
            result[0] = test_result
            window_result = {}
            for gid in self.gherkins.keys():
                prediction_key = f"prediction_{gid}"
                # window_result[prediction_key] = {}
                window_result[prediction_key] = {
                    "total_right_predictions": 0,
                    "total_wrong_predictions": 0,
                    "total_gain": 0,
                }
                count = 0
                for df in test_result:
                    for index, row in df.iterrows():
                        if row[prediction_key] == "right":
                            window_result[prediction_key][
                                "total_right_predictions"
                            ] += 1
                        elif row[prediction_key] == "wrong":
                            window_result[prediction_key][
                                "total_wrong_predictions"
                            ] += 1
                        window_result[prediction_key]["total_gain"] += row[
                            f"gain%_{prediction_key}"
                        ]
                    count += 1
                    df.to_csv(f"test_{count}_{window}.csv", index=False)
            for k, v in window_result.items():
                print(
                    f"""
                    id: {k}\n \
                    total_right_predictions: {v["total_right_predictions"]}\n\
                    total_wrong_predictions: {v["total_wrong_predictions"]}\n\
                    total_gain: {v["total_gain"]}\n"""
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
    gherkin1 = f"""Feature: v2\n
    Scenario: {SCENARIO}\n
    Given stocks from index nifty50\n
    When let ema10Change = rate in 10 samples of minute5 close ema 10\n
    * let vwap10Change = rate in 10 samples of minute5 close vwap 10\n
    * let ema10Day = latest in 1 samples of day close ema 10\n
    * let close = latest in 1 samples of minute5 close\n
    Then let inrange = close > ema10Day * 0.99 and close < ema10Day * 1.01\n
    * list bull = tickers with ema10Change > 0 and vwap10Change > 0 and inrange\n
    * list bear = tickers with ema10Change < 0 and vwap10Change < 0 and inrange\n
    """
    gherkin2 = f"""Feature: v2\n
    Scenario: {SCENARIO}\n
    Given stocks from index nifty50\n
    When let ema10Change = rate in 10 samples of minute5 close ema 10\n
    * let vwap10Change = rate in 10 samples of minute5 close vwap 10\n
    * let vwapMax = maximum in 10 samples of minute5 close vwap 10\n
    * let vwapMin = minimum in 10 samples of minute5 close vwap 10\n
    * let emaMax = maximum in 10 samples of minute5 close ema 10\n
    * let emaMin = minimum in 10 samples of minute5 close ema 10\n
    * let ema10Day = oldest in 2 samples of day close ema 10\n
    * let close = latest in 1 samples of minute5 close\n
    * let dayClose = oldest in 2 samples of day close\n
    Then let inrange = close > ema10Day * 0.99 and close < ema10Day * 1.01\n
    * list bull = tickers with ema10Change > 0 and vwap10Change > 0 and abs(dayClose - close) / dayClose > 0.01 and inrange\n
    * list bear = tickers with ema10Change < 0 and vwap10Change < 0 and abs(dayClose - close) / dayClose > 0.01 and inrange\n
    """
    gherkin3 = f"""Feature: v2\n
    Scenario: {SCENARIO}\n
    Given stocks from index nifty50\n
    When let ema10Change = rate in 10 samples of minute5 close ema 10\n
    * let vwap10Change = rate in 10 samples of minute5 close vwap 10\n
    * let vwapMax = maximum in 10 samples of minute5 close vwap 10\n
    * let vwapMin = minimum in 10 samples of minute5 close vwap 10\n
    * let emaMax = maximum in 10 samples of minute5 close ema 10\n
    * let emaMin = minimum in 10 samples of minute5 close ema 10\n
    * let ema10Day = oldest in 2 samples of day close ema 10\n
    * let close = latest in 1 samples of minute5 close\n
    * let dayClose = oldest in 2 samples of day close\n
    Then let inrange = close > ema10Day * 0.99 and close < ema10Day * 1.01\n
    * list bull = tickers with ema10Change > 0 and vwap10Change > 0 and abs(dayClose - close) / dayClose > 0.01\n
    * list bear = tickers with ema10Change < 0 and vwap10Change < 0 and abs(dayClose - close) / dayClose > 0.01\n
    """
    gherkin4 = f"""Feature: v2\n
    Scenario: {SCENARIO}\n
    Given stocks from index nifty50\n
    When let ema10Change = rate in 10 samples of minute5 close ema 10\n
    * let vwap10Change = rate in 10 samples of minute5 close vwap 10\n
    * let vwap = latest in 1 samples of minute5 close vwap 10\n
    * let vwapMin = minimum in 10 samples of minute5 close vwap 10\n
    * let emaMax = maximum in 10 samples of minute5 close ema 10\n
    * let emaMin = minimum in 10 samples of minute5 close ema 10\n
    * let ema10Day = oldest in 2 samples of day close ema 10\n
    * let close = latest in 1 samples of minute5 close\n
    * let dayClose = oldest in 2 samples of day close\n
    Then let vwaprange = abs(close - vwap) / close < 0.03 \n
    * list bull = tickers with ema10Change > 0 and vwap10Change > 0 and abs(dayClose - close) / dayClose > 0.01 and vwaprange\n
    * list bear = tickers with ema10Change < 0 and vwap10Change < 0 and abs(dayClose - close) / dayClose > 0.01 and vwaprange\n
    """
    gherkin5 = f"""Feature: v2\n
    Scenario: {SCENARIO}\n
    Given stocks from index nifty50\n
    When let ema10Change = rate in 10 samples of minute5 close ema 10\n
    * let vwap10Change = rate in 10 samples of minute5 close vwap 10\n
    * let vwap = latest in 1 samples of minute5 close vwap 10\n
    * let high = latest in 1 samples of minute5 high\n
    * let low = latest in 1 samples of minute5 low\n
    Then list bull = tickers with ema10Change > 0 and vwap10Change > 0 and (high > vwap and vwap > low)\n
    * list bear = tickers with ema10Change < 0 and vwap10Change < 0 and (high > vwap and vwap > low)\n
    """
    gherkin6 = f"""Feature: v2\n
    Scenario: {SCENARIO}\n
    Given stocks from index nifty50\n
    When let ema10Change = rate in 10 samples of minute5 close ema 10\n
    * let vwap10Change = rate in 10 samples of minute5 close vwap 10\n
    * let vwap = latest in 1 samples of minute5 close vwap 10\n
    * let high = latest in 1 samples of minute5 high\n
    * let low = latest in 1 samples of minute5 low\n
    Then list bull = tickers with ema10Change > 0 and (high > vwap and vwap > low)\n
    * list bear = tickers with ema10Change < 0 and (high > vwap and vwap > low)\n
    """
    gherkin7 = f"""Feature: v2\n
    Scenario: {SCENARIO}\n
    Given stocks from index nifty50\n
    When let ema10Change = rate in 10 samples of minute5 close ema 10\n
    * let vwap10Change = rate in 10 samples of minute5 close vwap 10\n
    * let vwap = latest in 1 samples of minute5 close vwap 10\n
    * let high = latest in 1 samples of minute5 high\n
    * let low = latest in 1 samples of minute5 low\n
    Then list bull = tickers with vwap10Change > 0 and (high > vwap and vwap > low)\n
    * list bear = tickers with vwap10Change < 0 and (high > vwap and vwap > low)\n
    """
    gherkin8 = f"""Feature: v2\n
    Scenario: {SCENARIO}\n
    Given stocks from index nifty50\n
    When let vwap = oldest in 2 samples of minute5 close vwap 10\n
    * let high = oldest in 2 samples of minute5 high\n
    * let low = oldest in 2 samples of minute5 low\n
    * let highT0 = latest in 1 samples of minute5 high\n
    * let lowT0 = latest in 1 samples of minute5 low\n
    Then list bull = tickers with highT0 > high and (high > vwap and vwap > low)\n
    * list bear = tickers with lowT0 < low and (high > vwap and vwap > low)\n
    """
    gherkins = {
        "inrange": gherkin1,
        "moversWithEmaVwapRiseAndRange": gherkin2,
        "moversWithEmaVwapRise": gherkin3,
        "vwapRange": gherkin4,
        "vwapTouchAndEmaVwapChange": gherkin5,
        "vwapTouchAndEmaChange": gherkin6,
        "vwapTouchAndVwapChange": gherkin7,
        "vwapTouch": gherkin8,
    }
    count = 1

    for window in range(2, 10, 4):
        # for name, gherkin in gherkins.items():
        print(f"-----{window}-----")
        ut = GherkinBacktest(
            indicator_config_file=indicator_config_yaml,
            selected_stocks_config_file=selected_stocks_yaml,
            command_handler=None,
            parameter={
                "window": window,
                "interval": "minute5",
                "n": 100,
                # "gherkin": gherkin,
                "TEST": gherkins,
            },
            name="",
        )
        res = ut.debug().obj
        # res.to_csv("test.csv")
    # count += 1

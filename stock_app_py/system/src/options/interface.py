import logging
import os
import re
import subprocess
import time
import numpy as np
import pandas
import csv
from datetime import datetime

from stock_app_py.system.src.yahoo_finance import YahooFinance
from stock_app_py.utility.src.path_helper import get_app_path
from stock_app_py.utility.src import date_helper
from stock_app_py.system.base.system import System
from stock_app_py.system.interface.system_if import RetVal
from stock_app_py.system.src.options.chain import OptionChain
from stock_app_py.system.src.options import price as option_price


class OptionInterface(System):
    def __init__(
        self,
        indicator_config_file: str,
        selected_stocks_config_file: str,
        parameter: dict,
        command_handler: object,
        name="",
    ) -> None:
        """Calculate option price using Black-scholes model.

        e.g.
        1. options --do get --ticker ADANIPORTS --date 29-Jan-2025
        2. options --do compare
        Args:
            indicator_config_file (str): indicator configuration
            selected_stocks_config_file (str): selected stocks list
            parameter (dict): key-value pairs for setting up the query
            command_handler (object): to call other systems
            name (str, optional): Name of the query. Defaults to "".
        """
        super().__init__(
            indicator_config_file=indicator_config_file,
            selected_stocks_config_file=selected_stocks_config_file,
            parameter=parameter,
            command_handler=command_handler,
            name=name,
        )
        self.yahoofin = YahooFinance(
            indicator_config_file=indicator_config_file,
            selected_stocks_config_file=indicator_config_file,
            parameter={},
            command_handler=None,
            name="",
        )
        self.commands = {"get": self.__get}
        self.option_chain = OptionChain()

    def __get(self) -> RetVal:
        result = (None, "")
        try:
            result = self.__calculate_probable_price_till_expiry(
                ticker=self.parameter["ticker"], start_date=self.parameter["date"]
            )
        except Exception as e:
            logging.error(e)
        return RetVal(
            obj=result[0], obj_as_str="probable option price", errors=result[1]
        )

    def __calculate_probable_price_till_expiry(self, ticker: str, start_date: str):
        """Compute the option price.
        Returns:
            RetVal: return object to be send to client
        """
        try:
            ohlc = self.yahoofin.read_ohlc(
                interval=self.parameter["interval"], ticker=ticker
            ).obj

            option_chain = self.option_chain.requestNseOptionChain(
                ticker=self.parameter["ticker"], isIndex=False  # TODO
            )
            result = []
            for expiry, rows in option_chain.items():
                result_for_expiry = []
                days_to_expiry = date_helper.days_until(
                    start_date=start_date if start_date != "" else "today",
                    target_date=expiry,
                    date_format="%d-%b-%Y",
                )
                today_to_expiry = date_helper.days_until(
                    start_date="today",
                    target_date=expiry,
                    date_format="%d-%b-%Y",
                )
                annual_volatility = option_price.calculate_volatility(
                    ohlc=ohlc, trading_days=252
                )
                for row in rows:
                    if row["CE"]["openInterest"] > 0 and row["PE"]["openInterest"] > 0:
                        strike_price = row["strikePrice"]

                        upward_price, downward_price = option_price.future_stock_price(
                            ohlc=ohlc, period_in_days=days_to_expiry, std_dev=0.1
                        )
                        upward_option_price = option_price.calculate_option_prices(
                            current_stock_price=upward_price,
                            strike_price=strike_price,
                            days_to_expiry=days_to_expiry,
                            annual_volatility=annual_volatility,
                        )
                        downward_option_price = option_price.calculate_option_prices(
                            current_stock_price=downward_price,
                            strike_price=strike_price,
                            days_to_expiry=days_to_expiry,
                            annual_volatility=annual_volatility,
                        )
                        current_option_price = option_price.calculate_option_prices(
                            current_stock_price=ohlc.iloc[-1]["Close"],
                            strike_price=strike_price,
                            days_to_expiry=today_to_expiry,
                            annual_volatility=annual_volatility,
                        )

                        result_for_expiry.append(
                            {
                                "strike": strike_price,
                                "call": row["CE"]["lastPrice"],
                                "put": row["PE"]["lastPrice"],
                                "BSCall": round(current_option_price[0], 2),
                                "BSPut": round(current_option_price[1], 2),
                                "probabilities": {
                                    "date": start_date,
                                    "up": round(upward_price, 2),
                                    "down": round(downward_price, 2),
                                    "upCall": round(upward_option_price[0], 2),
                                    "upPut": round(upward_option_price[1], 2),
                                    "downCall": round(downward_option_price[0], 2),
                                    "downPut": round(downward_option_price[1], 2),
                                },
                            }
                        )
                result.append(
                    {
                        "expiry": expiry,
                        "data": result_for_expiry,
                        "open": ohlc.iloc[-1]["Open"],
                        "high": ohlc.iloc[-1]["High"],
                        "low": ohlc.iloc[-1]["Low"],
                        "close": ohlc.iloc[-1]["Close"],
                    }
                )
            return (result, "")
        except Exception as e:
            logging.error(e)
            return (None, e)

    def __get_expiry_dates(self, isIndex=False) -> list:
        return list(
            self.option_chain.requestNseOptionChain(
                ticker=self.parameter["ticker"], isIndex=isIndex
            ).keys()
        )

    def debug(self):
        return self.__get()


if __name__ == "__main__":
    indicator_config_yaml = get_app_path("indicator.yaml")
    selected_stocks_yaml = get_app_path("selected_stocks.yaml")
    parameter = {"ticker": "ADANIPORTS", "interval": "day", "date": "28-Jan-2025"}
    oi = OptionInterface(
        indicator_config_file=indicator_config_yaml,
        selected_stocks_config_file=selected_stocks_yaml,
        parameter=parameter,
        command_handler=None,
        name="",
    )
    yf = YahooFinance(
        indicator_config_file=indicator_config_yaml,
        selected_stocks_config_file=selected_stocks_yaml,
        parameter=parameter,
        command_handler=None,
        name="",
    )
    ohlc = oi.debug().obj

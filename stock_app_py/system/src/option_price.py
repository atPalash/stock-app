import os
import re
import subprocess
import time
import numpy as np
import pandas
import csv
import statistics
from blackscholes import BlackScholesCall, BlackScholesPut

from stock_app_py.system.src.yahoo_finance import YahooFinance
from stock_app_py.utility.src.path_helper import get_app_path
from stock_app_py.utility.src.yaml_parser import read_config
from stock_app_py.system.base.system import System
from stock_app_py.system.interface.system_if import RetVal
from stock_app_py.system.src.steps.given import aggregator as given_aggregator
from stock_app_py.system.src.steps.when import aggregator as when_aggregator
from stock_app_py.system.src.steps.then import aggregator as then_aggregator


class OptionPrice(System):
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
        1. optionprice --do get --ticker ADANIPORTS
        2. optionprice --do compare
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
            indicator_config_file=indicator_config_yaml,
            selected_stocks_config_file=selected_stocks_yaml,
            parameter={},
            command_handler=None,
            name="",
        )
        self.commands = {"get": self.__get, "compare": self.__compare}

    def debug(self):
        return self.__get()

    def __get(self) -> RetVal:
        """Compute the option price.
        Returns:
            RetVal: return object to be send to client
        """
        ret = None
        err = ""
        try:
            df = self.yahoofin.read_ohlc(
                interval=self.parameter["interval"], ticker=self.parameter["ticker"]
            ).obj
            annualised_daily_volatility = self.__calculate_volatility(df, 252)
            option_price = self.__calculate_option_prices(
                S=1094.15,
                K=1100,
                T=32 / 252,
                r=0.07,
                sigma=annualised_daily_volatility,
                q=0,
            )
            print(annualised_daily_volatility)
        except Exception as e:
            err = e.args[0]
        return RetVal(obj=ret, obj_as_str="dict of option´price", errors=err)

    def __compare():
        pass

    def __calculate_volatility(self, df, multiplier):
        data = df[["Date", "Close"]]
        data["logRelativePrice"] = 0
        for i in range(1, len(data.Date)):
            data["logRelativePrice"][i] = np.log(
                data["Close"][i] / data["Close"][i - 1]
            )
        volatility = statistics.stdev(data["logRelativePrice"])
        return volatility * np.sqrt(multiplier)

    def __calculate_option_prices(self, S, K, T, r, sigma, q):
        """
        Calculate the Black-Scholes option prices for European call and put options using the 'blackscholes' package.

        Parameters:
        S : float - current stock price
        K : float - strike price of the option
        T : float - time to maturity (in years)
        r : float - risk-free interest rate (annual as a decimal)
        sigma : float - volatility of the underlying stock (annual as a decimal)
        q : float - annual dividend yield (as a decimal)

        Returns:
        tuple - (call price, put price)
        """
        # Creating instances of BlackScholesCall and BlackScholesPut
        call_option = BlackScholesCall(S=S, K=K, T=T, r=r, sigma=sigma, q=q)
        put_option = BlackScholesPut(S=S, K=K, T=T, r=r, sigma=sigma, q=q)

        # Get call and put prices
        call_price = call_option.price()
        put_price = put_option.price()

        return call_price, put_price


if __name__ == "__main__":
    indicator_config_yaml = get_app_path("indicator.yaml")
    selected_stocks_yaml = get_app_path("selected_stocks.yaml")
    yf = OptionPrice(
        indicator_config_file=indicator_config_yaml,
        selected_stocks_config_file=selected_stocks_yaml,
        parameter={"ticker": "ADANIPORTS", "interval": "day"},
        command_handler=None,
        name="",
    )
    # https://www.niftyindices.com/IndexConstituent/ind_niftyautolist.csv
    # https://www.niftyindices.com/IndexConstituent/nifty_low_Volatility50_Index.csv
    # https://www.niftyindices.com/IndexConstituent/ind_niftyoilgaslist.csv
    # javascript:;
    start_time = time.time()
    print(yf.debug().obj)
    print("--- %s seconds ---" % (time.time() - start_time))
    # print(data.obj)

from flask import jsonify
import numpy as np
import pandas
import nsepython

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
        2. options --do find --ticker ADANIPORTS --date 29-Jan-2025 --std_deviation 0.7 --n 4 --strategies ironCondor, bullCallSpread, bullPutSpread
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
        self.commands = {"get": self.__get, "find": self.__find}
        self.nse_option_chain = OptionChain()
        self.base_strategies_class = [IronCondor, Spread]

    def __get(self) -> RetVal:
        result = [None, ""]
        try:
            ohlc = self.yahoofin.read_ohlc(
                interval=self.parameter["interval"], ticker=self.parameter["ticker"]
            ).obj
            result = self.calculate_probable_price_till_expiry(ohlc=ohlc)
        except Exception as e:
            logger.error(e)
        return RetVal(
            obj=result[0], obj_as_str="probable option price", errors=result[1]
        )

    def __find(self) -> RetVal:
        result = [None, ""]
        try:
            strategies_to_search = (
                self.parameter["strategies"].replace(" ", "").split(",")
            )
            ohlc = self.yahoofin.read_ohlc(
                interval=self.parameter["interval"], ticker=self.parameter["ticker"]
            ).obj

            nse_python = nsepython.nse_quote(
                symbol=self.nse_option_chain._formatIndexSymbol(
                    self.parameter["ticker"]
                )
            )
            filter_nse_python = nse_python["stocks"][0]["marketDeptOrderBook"]
            lot_size = filter_nse_python["tradeInfo"]["marketLot"]
            # lot_size = 0

            daily_volatility = price.calculate_volatility(ohlc=ohlc, trading_days=1)
            today_to_date = date_helper.days_until(
                start_date="today",
                target_date=(
                    self.parameter["date"] if self.parameter["date"] != "" else "today"
                ),
                date_format="%d-%b-%Y",
            )
            upward_price, downward_price = price.future_stock_price(
                current_price=ohlc.iloc[-1]["Close"],
                period_in_days=today_to_date,
                std_dev=self.parameter["std_deviation"],
                volatility=(daily_volatility * np.sqrt(today_to_date)),
            )
            upward_price = round(upward_price, 2)
            downward_price = round(downward_price, 2)

            result_dict = self.__find_best_N_strategy(
                strategies=strategies_to_search,
                n=self.parameter["n"],
                std_price=(upward_price, downward_price),
            )
            ret = {
                "ticker": self.parameter["ticker"],
                "lotsize": lot_size,
                "open": ohlc.iloc[-1]["Open"],
                "high": ohlc.iloc[-1]["High"],
                "low": ohlc.iloc[-1]["Low"],
                "close": ohlc.iloc[-1]["Close"],
                "stdDev": self.parameter["std_deviation"],
                "date": self.parameter["date"],
                "up": upward_price,
                "down": downward_price,
                "bsCall": {},
                "bsPut": {},
                "expirees": [],
            }
            for expiry, df in result_dict.items():
                ret["expirees"].append(
                    {"expiry": expiry, "data": df.to_dict(orient="records")}
                )

                days_to_expiry = date_helper.days_until(
                    start_date="today",
                    target_date=expiry,
                    date_format="%d-%b-%Y",
                )
                for strike in nse_python["strikePrices"]:
                    try:
                        black_scholz = price.calculate_option_prices(
                            S=strike,
                            K=ohlc.iloc[-1]["Close"],
                            T=days_to_expiry / 365,
                            r=0.07,
                            sigma=daily_volatility * np.sqrt(365),
                            q=0,
                        )
                        ret["bsCall"][strike] = black_scholz[0]
                        ret["bsPut"][strike] = black_scholz[1]
                    except Exception as e:
                        logger.info(e.args)

                # df.to_csv(f"{expiry}.csv", index=False)  # debug
            result[0] = jsonify(ret)
        except Exception as e:
            logger.error(e)
            result[1] = e.args
        return RetVal(
            obj=result[0], obj_as_str="probable option price", errors=result[1]
        )

    def __find_best_N_strategy(
        self, strategies: list, n: int, std_price: tuple
    ) -> dict:
        result = {}
        for strategy_class in self.base_strategies_class:
            self.parameter["n"] = n
            strategy = strategy_class(
                options_interface=self,
                parameter=self.parameter,
                indicator_config_file=self.indicator_config_file,
                selected_stocks_config_file=self.selected_stocks_config_file,
            )
            result_ticker = strategy.get(std_price, strategies)
            for expiry in result_ticker.keys():
                if expiry not in result:
                    result[expiry] = result_ticker[expiry]
                else:
                    result[expiry] = pandas.concat(
                        [result[expiry], result_ticker[expiry]], ignore_index=True
                    )
        return result

    def calculate_probable_price_till_expiry(self) -> tuple:
        """Fetch the current option prices at allowed strike prices for all
        the allowed expiries. Compute probable prices based on the user std_deviation
        and the proposed dates. This will allow compariesion to different option
        choices.

        Args:
            ticker (str): Calculate option prices for this ticker
            start_date (str): the date of calculation
            std_dev (float): probable standard deviation till start_date

        Returns:
            tuple:  0: list of option prices and probabilities
                    1: error string
        """
        try:
            nse_option_chain = self.nse_option_chain.requestNseOptionChain(
                ticker=self.parameter["ticker"]
            )

            result = []
            for expiry, rows in nse_option_chain.items():
                result_for_expiry = []
                for row in rows:
                    strike_price = row["strikePrice"]
                    result_for_expiry.append(
                        {
                            "strike": strike_price,
                            "call": row["CE"]["lastPrice"],
                            "put": row["PE"]["lastPrice"],
                            "call_oi": row["CE"]["openInterest"],
                            "put_oi": row["PE"]["openInterest"],
                        }
                    )
                result.append(
                    {
                        "expiry": expiry,
                        "data": result_for_expiry,
                    }
                )
            return (result, "")
        except Exception as e:
            logger.error(e)
            return (None, e)

    def get_probable_price(self, ticker: str, target_date: str, std_dev: float) -> list:
        ohlc = self.yahoofin.read_ohlc(interval="day", ticker=ticker).obj
        days_till = date_helper.days_until(
            start_date="today",
            target_date=target_date if target_date != "" else "today",
            date_format="%d-%b-%Y",
        )
        daily_volatility = price.calculate_volatility(ohlc=ohlc, trading_days=1)
        return price.future_stock_price(
            current_price=ohlc.iloc[-1]["Close"],
            period_in_days=days_till,
            std_dev=std_dev,
            volatility=(daily_volatility * np.sqrt(days_till)),
        )

    def debug(self):
        return self.__find()


if __name__ == "__main__":
    indicator_config_yaml = get_app_path("indicator.yaml")
    selected_stocks_yaml = get_app_path("selected_stocks.yaml")
    parameter = {
        "ticker": "ADANIPORTS",
        "interval": "day",
        "date": "25-Mar-2025",
        "strategies": "bullCallSpread, bullPutSpread",
        "std_deviation": 0.2,
        "n": 4,
    }
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

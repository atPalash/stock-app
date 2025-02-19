import pandas

# from stock_app_py.system.src.options.interface import OptionInterface
from stock_app_py.utility.src import date_helper, helper
from stock_app_py.utility.src.path_helper import get_app_path
from stock_app_py.system.src.options.strategy.strategy import Strategy
from stock_app_py.utility.src.logger import get_logger

logger = get_logger(__name__)


class Spread(Strategy):
    def __init__(
        self,
        options_interface,
        parameter: dict,
        indicator_config_file: str,
        selected_stocks_config_file: str,
    ) -> None:
        """Implement Spread and strangle
        1. Bull call
                S CE ________
                    /
                   /
         _________/
                B CE
        2. Bull put
                S PE ________
                    /
                   /
         _________/
                B PE
        3. Bear call
            ________ B CE   
                    \
                     \ 
                      \_________
                        S CE
        4. Bear put
            ________ B PE   
                    \
                     \ 
                      \_________
                        S PE
        5. Neutral strangle
             SPE _________ BCE
                /         \ 
               /           \
        6. Long strangle
                \           /
                 \_________/ 
                 BPE      BCE
        7. Long straddle
                \  /
                 \/ 
                BPE, BCE
        Args:
            parameter (dict): _description_
            indicator_config_file (str): _description_
            selected_stocks_config_file (str): _description_
        """
        super().__init__(
            options_interface=options_interface,
            parameter=parameter,
            indicator_config_file=indicator_config_file,
            selected_stocks_config_file=selected_stocks_config_file,
        )
        self.supoorted = [
            "bullCallSpread",
            "bullPutSpread",
            "bearCallSpread",
            "bearPutSpread",
            "neutralStrangle",
            "longStrangle",
            "longStraddle",
        ]

    def get(self, std_dev_price: tuple, spreads: list):
        result = {}
        for spread in spreads:
            if spread not in self.supoorted:
                # logger.warning(f"{spread} is not supported")
                continue
            self.__calculate_price(spread=spread, std_dev_price=std_dev_price)
            result_ticker = self.expiry_output

            for expiry in result_ticker.keys():
                if expiry not in result:
                    result[expiry] = result_ticker[expiry]
                else:
                    result[expiry] = pandas.concat(
                        [result[expiry], result_ticker[expiry]], ignore_index=True
                    )
        return result

    def __calculate_price(self, spread, std_dev_price: tuple):
        option_chain = self.option_chain[0]
        ticker = self.parameter["ticker"]
        for row in option_chain:
            try:
                expiry = row["expiry"]
                proposed_date = self.parameter["date"]
                if date_helper.days_until(proposed_date, expiry) < 0:
                    logger.warning(
                        f"Spread not possible when proposed date {proposed_date} is greater than expiry {expiry}"
                    )
                    continue
                strikes = [item["strike"] for item in row["data"]]
                combinations = {
                    "BPE": [],
                    "SPE": [],
                    "SCE": [],
                    "BCE": [],
                }  # initialise from temp
                if spread == "bullCallSpread":
                    combinations["BCE"] = helper.find_nearest_N_numbers(
                        numbers=strikes, target=std_dev_price[1], N=self.parameter["n"]
                    )
                    combinations["SCE"] = helper.find_nearest_N_numbers(
                        numbers=strikes, target=std_dev_price[0], N=self.parameter["n"]
                    )
                elif spread == "bullPutSpread":
                    combinations["BPE"] = helper.find_nearest_N_numbers(
                        numbers=strikes, target=std_dev_price[1], N=self.parameter["n"]
                    )
                    combinations["SPE"] = helper.find_nearest_N_numbers(
                        numbers=strikes, target=std_dev_price[0], N=self.parameter["n"]
                    )
                elif spread == "bearCallSpread":
                    combinations["SCE"] = helper.find_nearest_N_numbers(
                        numbers=strikes, target=std_dev_price[1], N=self.parameter["n"]
                    )
                    combinations["BCE"] = helper.find_nearest_N_numbers(
                        numbers=strikes, target=std_dev_price[0], N=self.parameter["n"]
                    )
                elif spread == "bearPutSpread":
                    combinations["SPE"] = helper.find_nearest_N_numbers(
                        numbers=strikes, target=std_dev_price[1], N=self.parameter["n"]
                    )
                    combinations["BPE"] = helper.find_nearest_N_numbers(
                        numbers=strikes, target=std_dev_price[0], N=self.parameter["n"]
                    )
                elif spread == "neutralStrangle":
                    combinations["SCE"] = helper.find_nearest_N_numbers(
                        numbers=strikes, target=std_dev_price[0], N=self.parameter["n"]
                    )
                    combinations["SPE"] = helper.find_nearest_N_numbers(
                        numbers=strikes, target=std_dev_price[1], N=self.parameter["n"]
                    )
                elif spread == "longStrangle":
                    combinations["BCE"] = helper.find_nearest_N_numbers(
                        numbers=strikes, target=std_dev_price[0], N=self.parameter["n"]
                    )
                    combinations["BPE"] = helper.find_nearest_N_numbers(
                        numbers=strikes, target=std_dev_price[1], N=self.parameter["n"]
                    )
                elif spread == "longStraddle":
                    combinations["BCE"] = helper.find_nearest_N_numbers(
                        numbers=strikes, target=row["close"], N=self.parameter["n"]
                    )
                else:
                    logger.error(f"Unknown spread type {spread}")
                    raise Exception(f"Unknown spread type {spread}")

                self.expiry_output[expiry] = self.__get_option_price(
                    expiry_prices=row["data"],
                    strikes=combinations,
                    spread=spread,
                )
            except Exception as e:
                logger.error(
                    f"Spread not possible for {ticker} on expiry {expiry}, error: {e}"
                )

    def __get_option_price(
        self, expiry_prices: dict, strikes: dict, spread: str
    ) -> pandas.DataFrame:
        row_index = 0
        if spread in [
            "bullCallSpread",
            "bearCallSpread",
        ]:  # len(strikes["SCE"]) > 0 and len(strikes["BCE"]) > 0:
            for bc_strike in strikes["BCE"]:
                buy_call = self._fetch_price(
                    strike=bc_strike, key="call", expiry_prices=expiry_prices
                )
                for sc_strike in strikes["SCE"]:
                    sell_call = self._fetch_price(
                        strike=sc_strike, key="call", expiry_prices=expiry_prices
                    )
                    self.combination_table.loc[row_index] = {
                        "BPE": [0, 0],
                        "SPE": [0, 0],
                        "SCE": sell_call,
                        "BCE": buy_call,
                    }
                    row_index += 1
        elif spread in ["bearPutSpread", "bullPutSpread"]:
            for bp_strike in strikes["BPE"]:
                buy_put = self._fetch_price(
                    strike=bp_strike, key="put", expiry_prices=expiry_prices
                )
                for sp_strike in strikes["SPE"]:
                    sell_put = self._fetch_price(
                        strike=sp_strike, key="put", expiry_prices=expiry_prices
                    )
                    self.combination_table.loc[row_index] = {
                        "BPE": buy_put,
                        "SPE": sell_put,
                        "SCE": [0, 0],
                        "BCE": [0, 0],
                    }
                    row_index += 1
        elif spread in ["neutralStrangle"]:
            for sc_strike in strikes["SCE"]:
                sell_call = self._fetch_price(
                    strike=sc_strike, key="call", expiry_prices=expiry_prices
                )
                for sp_strike in strikes["SPE"]:
                    sell_put = self._fetch_price(
                        strike=sp_strike, key="put", expiry_prices=expiry_prices
                    )
                    self.combination_table.loc[row_index] = {
                        "BPE": [0, 0],
                        "SPE": sell_put,
                        "SCE": sell_call,
                        "BCE": [0, 0],
                    }
                    row_index += 1
        elif spread in ["longStrangle"]:
            for bc_strike in strikes["BCE"]:
                buy_call = self._fetch_price(
                    strike=bc_strike, key="call", expiry_prices=expiry_prices
                )
                for bp_strike in strikes["BPE"]:
                    buy_put = self._fetch_price(
                        strike=bp_strike, key="put", expiry_prices=expiry_prices
                    )
                    self.combination_table.loc[row_index] = {
                        "BPE": buy_put,
                        "SPE": [0, 0],
                        "SCE": [0, 0],
                        "BCE": buy_call,
                    }
                    row_index += 1
        elif spread in ["longStraddle"]:
            for bc_strike in strikes["BCE"]:
                buy_call = self._fetch_price(
                    strike=bc_strike, key="call", expiry_prices=expiry_prices
                )
                buy_put = self._fetch_price(
                    strike=bc_strike, key="put", expiry_prices=expiry_prices
                )
                self.combination_table.loc[row_index] = {
                    "BPE": buy_put,
                    "SPE": [0, 0],
                    "SCE": [0, 0],
                    "BCE": buy_call,
                }
                row_index += 1
        return self._get_best_n_combination(
            strategy=spread,
            compute_func=self.__compute_func,
            sort_by=self.parameter["sortby"],
            N=self.parameter["n"],
        )

    def __compute_func(self, spread, row: pandas.Series) -> pandas.Series:
        row["ticker"] = self.parameter["ticker"]
        row["pay"] = row["BPE"][0] + row["BCE"][0]
        row["get"] = row["SPE"][0] + row["SCE"][0]
        row["net"] = row["get"] - row["pay"]
        row["strategy"] = spread
        if spread == "bullCallSpread" or spread == "bearPutSpread":
            row["max_loss"] = abs(row["net"])
            row["max_gain"] = max(
                abs(row["BCE"][1] - row["SCE"][1]), abs(row["SPE"][1] - row["BPE"][1])
            ) - abs(row["net"])
        elif spread == "bearCallSpread" or spread == "bullPutSpread":
            row["max_loss"] = max(
                abs(row["BCE"][1] - row["SCE"][1]), abs(row["SPE"][1] - row["BPE"][1])
            ) - abs(row["net"])
            row["max_gain"] = abs(row["net"])
        elif spread == "neutralStrangle":
            row["max_gain"] = abs(row["net"])
            row["max_loss"] = float("inf")
        elif spread == "longStrangle":
            row["max_gain"] = float("inf")
            row["max_loss"] = abs(row["net"])
        elif spread == "longStraddle":
            row["max_gain"] = float("inf")
            row["max_loss"] = abs(row["net"])
        else:
            logger.error(f"Unknown spread {spread}")
        row["risk_ratio"] = (
            1 if row["max_loss"] == 0 else row["max_gain"] / row["max_loss"]
        )
        row["BCE_strike"] = row["BCE"][1]
        row["SCE_strike"] = row["SCE"][1]
        row["BPE_strike"] = row["BPE"][1]
        row["SPE_strike"] = row["SPE"][1]
        return row

    def debug(self, types):
        self.get(spreads=types)


# if __name__ == "__main__":
#     indicator_config_yaml = get_app_path("indicator.yaml")
#     selected_stocks_yaml = get_app_path("selected_stocks.yaml")
#     parameter = {
#         "ticker": "SUNPHARMA",
#         "interval": "day",
#         "date": "10-Feb-2025",
#         "std_deviation": 0.2,
#         "n": 2,
#         "spreadtype": "all",
#         "sortby": "max_gain",
#     }

#     ic = Spread(
#         parameter=parameter,
#         selected_stocks_config_file=selected_stocks_yaml,
#         indicator_config_file=indicator_config_yaml,
#     )

#     ic.debug(types=["bullCallSpread", "bullPutSpread"])

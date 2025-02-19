import pandas

# from stock_app_py.system.src.options.interface import OptionInterface
from stock_app_py.utility.src import date_helper, helper
from stock_app_py.utility.src.path_helper import get_app_path
from stock_app_py.system.src.options.strategy.strategy import Strategy
from stock_app_py.utility.src.logger import get_logger

logger = get_logger(__name__)


class IronCondor(Strategy):
    def __init__(
        self,
        options_interface,
        parameter: dict,
        indicator_config_file: str,
        selected_stocks_config_file: str,
    ) -> None:
        """Implement Iron condor
                S PE  _________________________  S CE
                    /                          \
                   /                            \ 
         _________/                              \___________
                B PE                                B CE

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
        self.supoorted = ["ironCondor"]

    def get(
        self,
        std_dev_price: tuple,
        types=[],
    ):
        for strategy in types:
            if strategy not in self.supoorted:
                # logger.warning(f"{strategy} not supported by this class")
                continue
            self.__calculate_price(strategy=strategy, std_dev_price=std_dev_price)
        return self.expiry_output

    def __calculate_price(self, strategy, std_dev_price):
        option_chain = self.option_chain[0]
        ticker = self.parameter["ticker"]
        probable_price_limit = self.option_interface.get_probable_price(
            ticker=ticker,
            target_date=self.parameter["date"],
            std_dev=self.parameter["std_deviation"] * 2,  # limiting the Buy CE AND PE
        )

        for row in option_chain:
            try:
                expiry = row["expiry"]
                proposed_date = self.parameter["date"]
                if date_helper.days_until(proposed_date, expiry) < 0:
                    logger.warning(
                        f"Iron condor not possible when proposed date {proposed_date} is greater than expiry {expiry}"
                    )
                    continue
                strikes = [item["strike"] for item in row["data"]]
                combinations = {
                    "BPE": [],
                    "SPE": [],
                    "SCE": [],
                    "BCE": [],
                }  # initialise from temp
                nearest_sell_ce = helper.find_nearest_N_numbers(
                    numbers=strikes, target=std_dev_price[0], N=self.parameter["n"]
                )
                nearest_sell_pe = helper.find_nearest_N_numbers(
                    numbers=strikes, target=std_dev_price[1], N=self.parameter["n"]
                )
                nearest_buy_ce = helper.find_nearest_N_numbers(
                    numbers=strikes,
                    target=probable_price_limit[0],
                    N=self.parameter["n"],
                )
                nearest_buy_pe = helper.find_nearest_N_numbers(
                    numbers=strikes,
                    target=probable_price_limit[1],
                    N=self.parameter["n"],
                )
                combinations["BPE"] = nearest_buy_pe
                combinations["SPE"] = nearest_sell_pe
                combinations["SCE"] = nearest_sell_ce
                combinations["BCE"] = nearest_buy_ce
                self.expiry_output[expiry] = self.__get_option_price(
                    expiry_prices=row["data"], strikes=combinations, strategy=strategy
                )
            except Exception as e:
                logger.error(
                    f"Iron condor not possible for {ticker} on expiry {expiry}"
                )

    def __get_option_price(
        self, expiry_prices: dict, strikes: dict, strategy: str
    ) -> pandas.DataFrame:
        row_index = 0
        for bp_strike in strikes["BPE"]:
            buy_put = self._fetch_price(
                expiry_prices=expiry_prices, strike=bp_strike, key="put"
            )
            for sp_strike in strikes["SPE"]:
                sell_put = self._fetch_price(
                    expiry_prices=expiry_prices, strike=sp_strike, key="put"
                )
                for sc_strike in strikes["SCE"]:
                    sell_call = self._fetch_price(
                        expiry_prices=expiry_prices, strike=sc_strike, key="call"
                    )
                    for bc_strike in strikes["BCE"]:
                        buy_call = self._fetch_price(
                            expiry_prices=expiry_prices, strike=bc_strike, key="call"
                        )
                        self.combination_table.loc[row_index] = {
                            "BPE": buy_put,
                            "SPE": sell_put,
                            "SCE": sell_call,
                            "BCE": buy_call,
                        }
                        row_index += 1
        return self._get_best_n_combination(
            strategy=strategy,
            compute_func=self.__compute_func,
            sort_by=self.parameter["sortby"],
            N=self.parameter["n"],
        )

    def __compute_func(self, strategy, row: pandas.Series) -> pandas.Series:
        row["ticker"] = self.parameter["ticker"]
        row["pay"] = row["BPE"][0] + row["BCE"][0]
        row["get"] = row["SPE"][0] + row["SCE"][0]
        row["net"] = row["get"] - row["pay"]
        row["max_loss"] = abs(
            max((row["BCE"][1] - row["SCE"][1]), (row["SPE"][1] - row["BPE"][1]))
            - row["net"]
        )
        row["max_gain"] = abs(row["net"])
        row["risk_ratio"] = (
            1 if row["max_loss"] == 0 else row["max_gain"] / row["max_loss"]
        )
        row["strategy"] = strategy
        row["BCE_strike"] = row["BCE"][1]
        row["SCE_strike"] = row["SCE"][1]
        row["BPE_strike"] = row["BPE"][1]
        row["SPE_strike"] = row["SPE"][1]
        return row


# if __name__ == "__main__":
#     indicator_config_yaml = get_app_path("indicator.yaml")
#     selected_stocks_yaml = get_app_path("selected_stocks.yaml")
#     parameter = {
#         "ticker": "TCS",
#         "interval": "day",
#         "date": "10-Feb-2025",
#         "std_deviation": 1,
#         "n": 2,
#     }

#     ic = IronCondor(
#         parameter=parameter,
#         selected_stocks_config_file=selected_stocks_yaml,
#         indicator_config_file=indicator_config_yaml,
#     )
#     print(ic.debug())

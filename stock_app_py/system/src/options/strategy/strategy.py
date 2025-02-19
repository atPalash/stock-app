import logging
import pandas


class Strategy:
    def __init__(
        self,
        options_interface,
        parameter: dict,
        selected_stocks_config_file: str,
        indicator_config_file: str,
    ) -> None:
        self.selected_stocks_config_file = selected_stocks_config_file
        self.indicator_config_file = indicator_config_file
        self.parameter = parameter
        self.combinations = {"BPE": [], "SPE": [], "SCE": [], "BCE": []}  # temp list
        self.combination_table = pandas.DataFrame(
            columns=list(self.combinations.keys())
        )
        self.option_interface = options_interface
        self.option_chain = self.option_interface.calculate_probable_price_till_expiry()
        if self.option_chain[1] != "":
            msg = f"Option calculation failed for {self.parameter['ticker']}"
            Exception(msg)
            logging.error(msg)

        self.expiry_output = {}

        self.output_format = {  # format for data analysis
            "pay": 0,
            "get": 0,
            "net_pay": 0,
            "max_loss": 0,
            "max_gain": 0,
            "risk_ratio": 0,
        }
        self.is_supported = []

    def get(self, types: list):
        pass

    def __calculate_price(self):
        pass

    def __get_option_price(self, expiry_prices: dict, strikes: dict) -> dict:
        pass

    def _get_best_n_combination(self, strategy, compute_func, sort_by: str, N=4):
        self.combination_table = self.combination_table.apply(
            lambda row: compute_func(strategy, row),
            axis=1,
        )
        # sorted_df = self.combination_table.sort_values(by=sort_by, ascending=False)
        # sorted_df.reset_index(drop=True, inplace=True)
        ret = self.combination_table
        ret.reset_index(drop=True, inplace=True)
        return ret.round(2)

    def _fetch_price(self, strike, expiry_prices, key):
        cost = next(filter(lambda row: row["strike"] == strike, expiry_prices), None)[
            key
        ]
        return [cost, strike]

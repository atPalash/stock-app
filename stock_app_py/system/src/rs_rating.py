import pandas

from stock_app_py.system.base.system import System
from stock_app_py.system.interface.system_if import RetVal


class RsRating(System):
    def __init__(
        self,
        indicator_config_file: str,
        selected_stocks_config_file: str,
        parameter: dict,
        command_handler: object,
        name="",
    ) -> None:
        """Calculate the price change to store IBD styled price change weightage.
        Save the price each day to a csv file. 2 query methods are supported.

        e.g. rsrating --do get, rsrating --do update
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

        self.commands = {
            "get": self.__get,
            "update": self.__update,
            "calculate": self.__calculate_change,
        }

    def __get(self) -> RetVal:
        """Return pandas dataframe of price changes as calculated in IBD. The client
        needs to calculate relative strength comparison according to requirements.

        Returns:
            RetVal: selected stock config
        """
        rs_rating_df = pandas.read_csv(f'{self.parameter["config_dir"]}/rs_rating.csv')
        return RetVal(
            obj=rs_rating_df, obj_as_str="pandas dataframe of rs rating", errors=""
        )

    def __update(self) -> RetVal:
        """Update the price change in the csv file.

        Returns:
            RetVal: price change object and errors
        """
        tickers_df_map = {}
        for ticker in self._get_tickers():
            ticker_ohlc_csv_path = (
                f'{self.indicator_config["indicator"]["data"]["month"]}/{ticker}.csv'
            )
            ticker_df = pandas.read_csv(ticker_ohlc_csv_path)
            tickers_df_map[ticker] = ticker_df

        ret = self.get_price_change(tickers_df_map=tickers_df_map)
        ret.obj.to_csv(f'{self.parameter["config_dir"]}/rs_rating.csv', index=False)
        return RetVal(
            obj=ret.obj, obj_as_str="rs rating csv created", errors=ret.errors
        )

    @staticmethod
    def __change(df: pandas.DataFrame):
        ending_value = df.iloc[-1]["Close"]
        beginning_value = df.iloc[0]["Close"]
        growth_rate = (ending_value - beginning_value) / beginning_value
        return growth_rate

    @staticmethod
    def __calculate_change(df: pandas.DataFrame):
        change_last_quarter_0 = 0
        change_last_quarter_1 = 0
        change_last_quarter_2 = 0
        change_last_quarter_3 = 0
        if len(df) >= 3:
            change_last_quarter_0 = RsRating.__change(df.iloc[-3:]) * 0.4
        if len(df) >= 6:
            change_last_quarter_1 = RsRating.__change(df.iloc[-6:-3]) * 0.2
        if len(df) >= 9:
            change_last_quarter_2 = RsRating.__change(df.iloc[-9:-6]) * 0.2
        if len(df) >= 12:
            change_last_quarter_3 = RsRating.__change(df.iloc[-12:-9]) * 0.2
        value = (
            change_last_quarter_0
            + change_last_quarter_1
            + change_last_quarter_2
            + change_last_quarter_3
        )
        return round(value, 5)

    def get_price_change(self, tickers_df_map: dict) -> RetVal:
        """The Relative Strength Rating is the result of calculating
        a stock's percentage price change over the last 12 months. A 40% weight is
        assigned to the latest three-month period; the remaining three quarters each
        receive 20% weight. All stocks are arranged in order of greatest price percentage
        change and assigned a percentile rank from 99 (highest) to 1 (lowest).

        Args:
            tickers_df_map (dict): a dict of ticker and ohlc dataframe

        Returns:
            RetVal: contains price change errors etc
        """
        tickers = []
        price_changes = []
        err = ""
        for key, val in tickers_df_map.items():
            try:
                tickers.append(key)
                price_changes.append(self.__calculate_change(df=val))
            except Exception as e:
                err += e.args
        data = {"ticker": tickers, "price_change": price_changes}
        rs_rating_df = pandas.DataFrame(data)
        rs_rating_df = rs_rating_df.sort_values("price_change")
        return RetVal(obj=rs_rating_df, obj_as_str="rs rating csv created", errors=err)

    def debug_update(self):
        self.__update()


if __name__ == "__main__":
    configFolder = "/home/palash/stock-app/configuration/"
    indicator_config_yaml = configFolder + "indicator.yaml"
    selected_stocks_yaml = configFolder + "selected_stocks.yaml"
    yf = RsRating(
        indicator_config_file=indicator_config_yaml,
        selected_stocks_config_file=selected_stocks_yaml,
        parameter={},
        command_handler=None,
        name="",
    )
    # https://www.niftyindices.com/IndexConstituent/ind_niftyautolist.csv
    # https://www.niftyindices.com/IndexConstituent/nifty_low_Volatility50_Index.csv
    # https://www.niftyindices.com/IndexConstituent/ind_niftyoilgaslist.csv
    # javascript:;
    data = yf.debug_update()
    print(data)

import numpy
import pandas
import json
from stock_app_py.system.base.system import System
from stock_app_py.system.interface.system_if import RetVal


class Webserver(System):
    def __init__(
        self,
        indicator_config_file: str,
        selected_stocks_config_file: str,
        parameter: dict,
        command_handler: object,
        name="",
    ) -> None:
        """Fetch the data based on requirements sent from HTML js. Here the HTML
        file request for different type of data based on the key indicator, generally
        this server fetches talib indicator data, but in addition we can also fetch
        other type of data based on map additional_indicators.

        e.g.
        GET
        1. webserver --ticker TCS --interval day --do get --indicator ohlc --n 1000 : get the ohlc data for 1000 candles
        This will call read the stored databased data and return.
        2. webserver --ticker TCS --interval day --do get --indicator ohlc --latest 1 : get the ohlc data for latest candles
        This will call yahoo finance and return latest data.
        3. webserver --ticker TCS --interval day --do get --indicator ema --n 1000 : get the ema data for 1000 candles
        This will call talib query and return ema values.

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

        self.commands = {"get": self.__get}

        self.interval = {"day": "1d", "hour": "1h", "week": "1wk"}
        self.periods = {"day": "5y", "hour": "2y", "week": "10y"}

        self.additional_indicators = {
            "tickers": self.__get_tickers,
            "ohlc": self.__get_ohlc,
            "macdhistdivergencescan": self.__get_macdhistdivergencescan,
            "elderimpulse": self.__get_elderimpulse,
            "canslim": self.__get_canslim,
            "macddivergencelist": self.__get_macddivergencelist,
            "stage2scanner": self.__getstage2scan,
            "gherkin": self.__getGherkinQuery,
        }

    def __get(self):
        """Get result of query received from HTML js. This"""
        tickers = self._get_tickers() + self._get_indices()
        ret_df = {}
        indicator = self.parameter["indicator"]
        err = ""
        if indicator == "tickers":
            # return the indicator list
            ret_df[indicator] = self.__get_tickers()
        elif indicator == "gherkin":
            gherkin_query = f'gherkinquery --gherkin {self.parameter["gherkin"]}'
            ret_df["gherkin"] = self.command_handler.execute(
                gherkin_query, is_rest=False
            ).obj_as_string
        elif indicator == "financials":
            financials_query = (
                f'yahoofinance --ticker {self.parameter["ticker"]} --do {indicator}'
            )
            ret_df[indicator] = self.command_handler.execute(
                financials_query, is_rest=False
            ).obj
        else:
            for ticker in tickers:
                try:
                    if self.additional_indicators.get(indicator):
                        ret_df[ticker] = self.additional_indicators[indicator](ticker)
                    else:
                        talib_query = f'talibquery --ticker {ticker} --interval {self.parameter["interval"]} --do get --csv 0 \
                            --indicator {indicator} --window {self.parameter["window"]} --n {self.parameter["n"]}'
                        df = self.command_handler.execute(
                            talib_query, is_rest=False
                        ).obj
                        df.set_index(df.iloc[:, 0], inplace=True)
                        ret_df[ticker] = df[indicator].to_json(orient="index")
                except Exception as e:
                    print("ERROR webserver __get")
                    err += e.args
        return RetVal(
            obj=ret_df, obj_as_str="python dict with pandas dataframe json", errors=err
        )

    def __get_tickers(self, *unused):
        return self._get_indices() + self._get_tickers()

    def __get_ohlc(self, ticker):
        ticker_ohlc_csv_path = f"{self.indicator_config['indicator']['data'][self.parameter['interval']]}/{ticker}.csv"
        return json.loads(
            pandas.read_csv(ticker_ohlc_csv_path, index_col=0)
            .tail(self.parameter["n"])
            .to_json(orient="index")
        )

    def __get_macdhistdivergencescan(self, ticker):
        col_name = "macdhist_divergence"
        macd_query = f'macdhistdivergencescan --ticker {ticker} --interval {self.parameter["interval"]} --do get \
                        --window {self.parameter["window"]} --n {self.parameter["n"]}'
        df = self.command_handler.execute(macd_query, is_rest=False).obj[ticker]
        df.set_index(df.iloc[:, 0], inplace=True)
        return df[col_name].to_json(orient="index")

    def __get_macddivergencelist(self, ticker):
        col_name = "macdhist_divergence"
        macd_query = f'macdhistdivergencescan --ticker {ticker} --interval {self.parameter["interval"]} --do get \
                        --window {self.parameter["window"]} --n {self.parameter["n"]}'
        df = self.command_handler.execute(macd_query, is_rest=False).obj[ticker]

        divergence_type = 0
        for i in df[col_name].iloc[::-1].index:
            val = df.loc[i][col_name]
            if val == 1:
                divergence_type = 1
                break
            elif val == -1:
                divergence_type = -1
                break
            else:
                divergence_type = 0
        return divergence_type

    def __get_elderimpulse(self, ticker):
        query = f'elderimpulse --ticker {ticker} --window {self.parameter["window"]} --do get --n {self.parameter["n"]} --macd_fast_period {self.parameter["macd_fast_period"]} --macd_slow_period {self.parameter["macd_slow_period"]} --macd_signal_period {self.parameter["macd_signal_period"]}'
        df = self.command_handler.execute(query, is_rest=False).obj
        return df.iloc[df[df["stock"] == ticker].index[0]].to_json()

    def __get_canslim(self, ticker):
        query = f'canslim --ticker {ticker} --interval {self.parameter["interval"]} --window {self.parameter["window"]} --do get --n {self.parameter["n"]}'
        df = self.command_handler.execute(query, is_rest=False).obj
        canslim = df[ticker]
        text = ""
        ret = {}
        if canslim is not None:
            ret["quaterly eps growth"] = canslim.C.pct_change(periods=-1).to_dict()
            ret["yearly eps growth"] = canslim.A.pct_change(periods=-1).to_dict()
            ret["relative strength"] = canslim.L.values.mean()
            ret["market direction"] = numpy.polyfit(
                canslim.M.index.values, canslim.M.values, 1
            )[0]
            ret["shares outstanding"] = canslim.S.to_dict()

        return json.dumps({"canslim": ret})

    def __getstage2scan(self, ticker):
        query = f'stage2scan --ticker {ticker} --interval {self.parameter["interval"]} \
            --window {self.parameter["window"]} --do get --n {self.parameter["n"]} \
            --stage2scannertype {self.parameter["stage2scannertype"]}'
        df = self.command_handler.execute(query, is_rest=False).obj
        return df.iloc[df[df["stock"] == ticker].index[0]].to_json()

    def __getGherkinQuery(self, gherkin_string: str):
        check = self.command_handler.execute(gherkin_string).obj
        return json.dumps({})

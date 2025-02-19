import talib
import numpy
import pandas
import pandas_ta as ta
from stock_app_py.talib.base.indicator import Indicator


class Vwap(Indicator):
    def __init__(self, ohlc, parameter, ticker: str, name="", type="") -> None:
        super().__init__(
            name=name, type=type, ticker=ticker, ohlc=ohlc, parameter=parameter
        )

    def _do_analysis(self, latest=1):
        self.parse_indicator_setting(self.parameter["indicator_setting"], ["window"])
        df = self.ohlc.copy()
        df.set_index(pandas.DatetimeIndex(df["Datetime"]), inplace=True)
        df.ta.vwap(anchor="D", append=True)
        df = df.reset_index(drop=True).bfill()
        self.ohlc["vwap"] = df["VWAP_D"].round(2)
        return self.ohlc["vwap"]

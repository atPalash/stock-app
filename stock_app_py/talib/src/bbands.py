import talib
import numpy
import pandas
from scipy.stats import linregress

from stock_app_py.talib.base.indicator import Indicator
from stock_app_py.yahoofinance.src.data_fetcher import download_latest_data


class Bbands(Indicator):
    def __init__(self, ohlc, parameter, ticker: str, name="", type="") -> None:
        super().__init__(
            name=name, type=type, ticker=ticker, ohlc=ohlc, parameter=parameter
        )

    def _do_analysis(self, latest=True):
        self.parse_indicator_setting(
            self.parameter["indicator_setting"], ["window", "std_deviation", "ma_type"]
        )
        upperband, middleband, lowerband = talib.BBANDS(
            self.ohlc[self.parameter["ohlc"]],
            int(self.parameter["window"]),
            int(self.parameter["std_deviation"]),
            int(self.parameter["std_deviation"]),
            int(self.parameter["ma_type"]),
        )
        if self.parameter["indicator"] == "upperbband":
            self.ohlc.loc[:, "upperbband"] = [round(num, 2) for num in upperband]
        elif self.parameter["indicator"] == "middlebband":
            self.ohlc.loc[:, "middlebband"] = [round(num, 2) for num in middleband]
        elif self.parameter["indicator"] == "lowerbband":
            self.ohlc.loc[:, "lowerbband"] = [round(num, 2) for num in lowerband]
        else:
            raise Exception("This should not happen")
        return self.ohlc[self.parameter["indicator"]].tolist()

from stock_app_py.talib.base.indicator import Indicator


class Rvol(Indicator):
    def __init__(self, ohlc, parameter, ticker: str, name="", type="") -> None:
        super().__init__(
            name=name, type=type, ticker=ticker, ohlc=ohlc, parameter=parameter
        )

    def _do_analysis(self, latest=1):
        self.parse_indicator_setting(self.parameter["indicator_setting"], ["window"])
        self.ohlc["avgVolume"] = (
            self.ohlc["Volume"].rolling(window=self.parameter["window"]).mean()
        )
        self.ohlc["rvol"] = self.ohlc["Volume"] / self.ohlc["avgVolume"]
        self.ohlc.drop(columns="avgVolume", inplace=True)
        return self.ohlc["rvol"]

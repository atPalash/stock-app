import logging
import requests
import pandas as pd

from pytick.utility.utility import get_logger

logger = get_logger(__file__, logging.DEBUG)

class NotificationHandler:
    def __init__(self, tz: str, tickers: list[str] = []):
        self.tz = tz
        self.corporate_actions = {} 

    def set_corporate_actions(self, tickers: list[str]) -> None:
        # Implementation for fetching notification
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0"
            }

            url = "https://www.nseindia.com/api/corporate-announcements?index=equities"

            with requests.session() as s:
                s.headers.update(headers)
                s.get(
                    "https://www.nseindia.com/companies-listing/corporate-filings-announcements",
                    timeout=100,
                )
                data = s.get(url).json()
                df = pd.DataFrame(data)
                df = df[df["symbol"].isin(tickers)]
                if not df.empty:
                    df = df.loc[
                        :, ["symbol", "desc", "attchmntFile", "attchmntText", "an_dt"]
                    ]
                    df.rename(
                        columns={
                            "an_dt": "date",
                            "desc": "subject",
                            "attchmntFile": "file",
                            "attchmntText": "details",
                        },
                        inplace=True,
                    )
                    df.reset_index(drop=True, inplace=True)
                    df["date"] = pd.to_datetime(df["date"])
                    df["date"] = df["date"].dt.strftime("%Y-%m-%d %H:%M:%S")
                    for ticker in tickers:
                        self.corporate_actions[ticker] = df[df["symbol"] == ticker]
        except Exception as e:
            logger.error(f"Error: {e.args}")

    def get_corporate_actions(self, tickers: list[str]) -> dict:
        ret = {}
        for ticker in tickers:
            ret[ticker] = self.corporate_actions.get(ticker, None)
        return ret

if __name__ == "__main__":
    nh = NotificationHandler(tz="Asia/Kolkata")
    nh.set_corporate_actions(tickers=["NTPC", "BEML", "INFY"])
    print(f"Corporate Announcements:\n {nh.get_corporate_actions(tickers=['NTPC', 'BEML', 'INFY'])}")

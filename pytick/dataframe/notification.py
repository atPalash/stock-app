import logging
import requests
import pandas as pd
import yfinance as yf
from pytick.utility.utility import get_logger
from pydantic import BaseModel

logger = get_logger(__file__, logging.DEBUG)

class NewsAlert(BaseModel):
    title: str = ""
    link: str = ""
    datetime: str = ""

class NotificationHandler:
    def __init__(self, tz: str = 'Asia/Kolkata', max_rows: int = 1000, app_data_path: str = ""):
        self.tz = tz
        self.corporate_actions = {}
        self.app_data_path = app_data_path
        try:
            self.corporate_actions_df = pd.read_csv(f"{self.app_data_path}/corporate_actions.csv", 
                parse_dates=['datetime'])
        except FileNotFoundError:
            self.corporate_actions_df = pd.DataFrame({
                "symbol": pd.Series(dtype="str"),
                "subject": pd.Series(dtype="str"),
                "file": pd.Series(dtype="str"),
                "details": pd.Series(dtype="str"),
                "datetime": pd.Series(dtype="datetime64[ns]")
            })
        self.max_rows = max_rows

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
                            "an_dt": "datetime",
                            "desc": "subject",
                            "attchmntFile": "file",
                            "attchmntText": "details",
                        },
                        inplace=True,
                    )
                    df.reset_index(drop=True, inplace=True)
                    df["datetime"] = pd.to_datetime(df['datetime'], format='%d-%b-%Y %H:%M:%S').\
                        dt.tz_localize(self.tz)
                    # df["datetime"] = df["datetime"].dt.strftime("%Y-%m-%d %H:%M:%S")
                    # Assign DataFrames for each ticker
                    for ticker in tickers:
                        self.corporate_actions[ticker] = df[df["symbol"] == ticker]
                    # Append all relevant rows to corporate_actions_df at once
                    # news_df = df[[col for col in self.corporate_actions_df.columns if col in df.columns]]
                    if not df.empty:
                        key_cols = ['symbol', 'subject', 'file', 'details', 'datetime']
                        self.corporate_actions_df = pd.concat([df, self.corporate_actions_df], ignore_index=True)\
                            .drop_duplicates(subset=key_cols, keep='last')\
                            .reset_index(drop=True)
                        if len(self.corporate_actions_df) > self.max_rows:
                            self.corporate_actions_df = self.corporate_actions_df.tail(self.max_rows).reset_index(drop=True)
                        self.corporate_actions_df.to_csv(f"{self.app_data_path}/corporate_actions.csv", index=False)                    
        except Exception as e:
            logger.warning(f"Exception: {e.args}")

    def get_corporate_actions(self, tickers: list[str]) -> dict:
        ret = {}
        for ticker in tickers:
            ret[ticker] = self.corporate_actions.get(ticker, None)
        return ret
    
    def get_corporate_actions_dfs(self, tickers: list[str]) -> dict:
        ret = {}
        for ticker in tickers:
            df = self.corporate_actions_df[self.corporate_actions_df["symbol"] == ticker]
            ret[ticker] = df if not df.empty else None
        return ret
    

if __name__ == "__main__":
    nh = NotificationHandler(tz="Asia/Kolkata")
    tickers = ["HAL", "COALINDIA", "INFY"]
    nh.set_corporate_actions(tickers=tickers)
    res = nh.get_corporate_actions_dfs(tickers=tickers)
    print(res)
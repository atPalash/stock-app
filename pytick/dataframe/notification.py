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
    date: str = ""

class NotificationHandler:
    def __init__(self, tz: str = 'Asia/Kolkata'):
        self.tz = tz
        self.corporate_actions = {}
        self.news_alerts = {}

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
    

    def set_news_alerts(self, tickers: list[str], limit: int = 5) -> None:
        """
        Fetch and store latest news for each ticker.
        """
        for ticker in tickers:
            try:
                ticker_obj = yf.Ticker(f"{ticker}.NS")
                news = ticker_obj.news[:limit] if hasattr(ticker_obj, 'news') else []
                alerts = []
                for item in news:
                    try:
                        content = item['content']
                        alerts.append(NewsAlert(title=content['title'], 
                                                link=content['canonicalUrl']['url'], 
                                                date=content['pubDate']).model_dump())
                    except Exception:
                        continue
                self.news_alerts[ticker] = alerts
            except Exception as e:
                logger.error(f"Error fetching news for {ticker}: {e}")
                self.news_alerts[ticker] = []

    def get_news_alerts(self, tickers: list[str], in_last: int=7, max_news: int = 3) -> dict[str, list[dict[str, str]]]:
        """
        Retrieve news alerts for each ticker within the last `in_last` days, limited to `max_news` items.
        """
        ret = {}
        date_threshold = pd.Timestamp.now(tz=self.tz) - pd.Timedelta(days=in_last)
        for ticker in tickers:
            ret[ticker] = None
            news_within_days = []
            try:
                for alert in self.news_alerts.get(ticker, []):
                    try:
                        if pd.to_datetime(alert['date']) >= date_threshold:
                            news_within_days.append(alert)
                        if len(news_within_days) >= max_news:
                            break
                    except Exception as e:
                        continue
            except Exception as e:
                continue
            if len(news_within_days) > 0:
                ret[ticker] = news_within_days
        return ret


if __name__ == "__main__":
    nh = NotificationHandler(tz="Asia/Kolkata")
    nh.set_corporate_actions(tickers=["NTPC", "BEML", "INFY"])
    print(f"Corporate Announcements:\n {nh.get_corporate_actions(tickers=['NTPC', 'BEML', 'INFY'])}")
    nh.set_news_alerts(tickers=["APOLLOHOSP", "SHRIRAMFIN", "NTPC"])
    print(f"News Alerts:\n {nh.get_news_alerts(tickers=['APOLLOHOSP', 'SHRIRAMFIN', 'NTPC'])}")

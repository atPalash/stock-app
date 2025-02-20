import yfinance as yf

data = yf.download(
    tickers=["BEL.NS"],
    period="1mo",
    interval="5m",
    progress=False,
    group_by="ticker",
    rounding=True,
    actions=True,
    threads=True,
    multi_level_index=False,
    ignore_tz=True,
)

data.to_csv("test.csv")

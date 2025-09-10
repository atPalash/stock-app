import yfinance as yf

def download_stock_data(ticker:str, interval:str, country:str="India")->None:
    data = yf.download(
        tickers=[f"{ticker}{".NS" if country=="India" else ""}"],
        period="max",
        interval=interval,
        progress=False,
        group_by="ticker",
        rounding=True,
        actions=True,
        threads=True,
        multi_level_index=False,
        ignore_tz=True,
        auto_adjust=True,
    )
    # data.to_csv(f"{ticker}.csv")
    return data

# download_stock_data("BEL", "15m")
# data.to_csv("test.csv")

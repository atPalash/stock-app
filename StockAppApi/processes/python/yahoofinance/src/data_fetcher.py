import yfinance as yf

def download_latest_data(tickers: list):
    data = yf.download(tickers=tickers, period='1d', interval='1m', 
                       progress=False, group_by="ticker", rounding=True, 
                       actions=True, threads=10, show_errors=True)
    data = data.dropna().tail(1)
    
def download_historical_data(tickers: list, period: int, interval: int, as_panda_df=False, 
                 as_csv=False, destination=""):
    data = yf.download(tickers=tickers, period=period, interval=interval, 
                       progress=False, group_by="ticker", rounding=True, 
                       actions=True, threads=10, show_errors=True)
    data = data.dropna()
    
    if as_csv:
        if destination != "":
            for ticker in tickers:
                csv_name = "{}/{}".format(destination, ticker.split(".")[0])
                if len(tickers) == 1:
                    data.to_csv(csv_name + '.csv')
                    break
                data[ticker].to_csv(csv_name + '.csv')
        else:
            raise FileNotFoundError("destination folder not defined") 
    
    if as_panda_df:
        return data
    
if __name__ == "__main__":
    try:
        download_historical_data(["ASIANPAINT.NS"], "10y", "1wk", True, True, "StockAppApi/database/test")
    except Exception as e:
        print(e.args)
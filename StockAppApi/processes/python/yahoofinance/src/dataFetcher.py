import yfinance as yf

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
                data[ticker].to_csv(csv_name + '.csv')
        else:
            raise FileNotFoundError("destination folder not defined") 
    
    if as_panda_df:
        return data
    
if __name__ == "__main__":
    try:
        download_historical_data(["TCS.NS", "TATAMOTORS.NS"], "1y", "1d", True, True, "database/test")
    except Exception as e:
        print(e.args)

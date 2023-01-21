import multiprocessing
import yfinance as yf

def __download_df_from_yahoo(tickers, period, interval):
    try:
        data = yf.download(tickers=tickers, period=period, interval=interval, 
                        progress=False, group_by="ticker", rounding=True, 
                        actions=True, threads=10, show_errors=True)
        data = data.dropna()
        return data
    except Exception as e:
        raise 

def __get_csv_from_yahoo(ticker, period, interval, destination):
    try:
        data = __download_df_from_yahoo(tickers=ticker, period=period, interval=interval)
        csv_name = "{}/{}".format(destination, ticker.split(".")[0])
        data.to_csv(csv_name + '.csv')
    except Exception as e:
        raise
    
def download_latest_data(tickers: list):
    try:
        data = yf.download(tickers=tickers, period='1d', interval='1m', 
                        progress=False, group_by="ticker", rounding=True, 
                        actions=True, threads=10, show_errors=True)
        data = data.dropna().tail(1)
    except Exception as e:
        raise
    
def download_historical_data(tickers: list, period: int, interval: int, as_panda_df=False, 
                 as_csv=False, destination=""):    
    """Download ohlc data from yahoo finance. When the desired return value is 
    pandas dataframe the number of rows are realligned to match dataframe for all
    the stocks, this causes dropping of older rows for some tickers, since the new
    tickers donot contain older data.
    
    Hence, for downloading to csv each ticker is downloaded as a separate ticker
    using multiple threads in parallel.

    Args:
        tickers (list): list of tickers
        period (int): maximum duration of data points. e.g. 5y, 10y, max
        interval (int): each row interval. e.g. 1d, 1h
        as_panda_df (bool, optional): return as pandas dataframe grouped by ticker. 
        Defaults to False.
        as_csv (bool, optional): download the tickers to csv. Defaults to False.
        destination (str, optional): path to where to download. Defaults to "".

    Returns:
        _type_: _description_
    """
    try:
        if as_csv:
            args = []
            for ticker in tickers:
                args.append((ticker, period, interval, destination))
            # Create a pool of worker processes
            with multiprocessing.Pool() as pool:
                pool.starmap(__get_csv_from_yahoo, args)
                
        if as_panda_df:
            return __download_df_from_yahoo(tickers=tickers, period=period, interval=interval)
    except Exception as e:
        raise
    
if __name__ == "__main__":
    try:
        download_historical_data(["ASIANPAINT.NS", "PREMEXPLN.NS"], "10y", "1wk", True, True, "StockAppApi/database/test")
    except Exception as e:
        print(e.args)
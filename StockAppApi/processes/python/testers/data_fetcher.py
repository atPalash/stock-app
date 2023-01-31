import multiprocessing
import yfinance as yf
import pandas
from StockAppApi.base.python.src.yaml_parser import read_config
import time

def __save_fundamentals_to_csv(original_df: pandas.DataFrame, filename:str):
    try:
        count = 0
        df = original_df
        while count < 5 and df.shape[0] == 0: 
            time.sleep(0.5)
            df = original_df
            count +=1
        if df.shape[0]>0:
            df.to_csv(f'{filename}')
    except Exception as e:
        print(e.args)

def __get_fundamentals_from_yahoo(ticker:str, destination:str)->None:
    try:
        info = yf.Ticker(ticker=ticker)
        name = ticker.split(".")[0]
        __save_fundamentals_to_csv(original_df=info.quarterly_financials, filename=f'{destination}/{name}_quarterly_financials.csv')
        __save_fundamentals_to_csv(original_df=info.quarterly_balancesheet, filename=f'{destination}/{name}_quarterly_balancesheet.csv')
        __save_fundamentals_to_csv(original_df=info.financials, filename=f'{destination}/{name}_financials.csv')
        __save_fundamentals_to_csv(original_df=info.institutional_holders, filename=f'{destination}/{name}_institutional_holders.csv')
    except Exception as e:
        raise

def download_stock_stats(tickers: list, destination):
    try:
        args = []
        for ticker in tickers:
            __get_fundamentals_from_yahoo(ticker=ticker, destination=destination)
            # args.append((ticker, destination))
            # # Create a pool of worker processes
            # with multiprocessing.Pool() as pool:
            #     pool.starmap(__get_fundamentals_from_yahoo, args)
    except Exception as e:
        raise

if __name__ == "__main__":
    try:
        selected_stocks = read_config("StockAppApi/configuration/selected_stocks.yaml")
        tickers = [tick + '.NS' for tick in selected_stocks['stock']]
        download_stock_stats(tickers=tickers, destination='/home/palash/dev/stock-app/StockAppApi/database/fundamentals')
        check =pandas.read_csv("/home/palash/dev/stock-app/StockAppApi/database/fundamentals/HDFC_quarterly_financials.csv")
        print(check.index)
    except Exception as e:
        print(e.args)

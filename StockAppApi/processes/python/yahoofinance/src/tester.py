import time

import pandas
import yfinance as yahooFinance

start = time.time()

nse_stocks = pandas.read_csv("/home/palash/dev/stock-app/StockAppApi/processes/python/yahoofinance/src/ind_nifty100list.csv")
nse_stock_information = pandas.DataFrame()

debug = True
stock_count = 0
try:
    for index, row in nse_stocks.iterrows():
        stock_information = yahooFinance.Ticker(row['Symbol'] + '.NS')
        column_names = []

        if index == 0:
            column_names = stock_information.info.keys()
            nse_stock_information = pandas.DataFrame(columns=column_names)

        nse_stock_information.loc[index] = stock_information.info
        stock_count += 1

except Exception as e:
    print(e)

print(nse_stock_information.shape)
nse_stock_information.to_csv("/home/palash/dev/stock-app/StockAppApi/processes/python/yahoofinance/src/stock_information.csv", index=False)
print("Elapsed ", time.time() - start)
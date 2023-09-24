from yahoofinancials import YahooFinancials
import json 

tickers = ['ABB.NS', 'TCS.NS', 'BEL.NS']

# proxy_addresses = [ "mysuperproxy.com:5000", "mysuperproxy.com:5001"]
yahoo_financials = YahooFinancials(tickers)
balance_sheet_data_qt = yahoo_financials.get_financial_stmts('quarterly', 'income')

with open("test.json", "w") as fp:
    json.dump(balance_sheet_data_qt,fp)

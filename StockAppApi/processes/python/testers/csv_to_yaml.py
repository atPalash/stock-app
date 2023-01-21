import pandas
import yaml

nify_100_list = pandas.read_csv("StockAppApi/processes/python/testers/ind_nifty100list.csv")
stocks = []
for _, row in nify_100_list.iterrows():
    stocks.append(row['Symbol'])
    
yaml_dict = {'stock': stocks}

with open('StockAppApi/processes/python/testers/selected_stocks.yaml', 'w') as outfile:
    yaml.dump(yaml_dict, outfile, default_flow_style=False)
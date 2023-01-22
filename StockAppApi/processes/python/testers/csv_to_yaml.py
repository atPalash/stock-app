# import pandas
# import yaml
# from StockAppApi.base.python.src.yaml_parser import read_config

# nify_list = pandas.read_csv("/home/palash/dev/stock-app/StockAppApi/processes/python/testers/data.csv")
# selected_list = read_config("/home/palash/dev/stock-app/StockAppApi/processes/python/testers/selected_stocks copy.yaml")
# stocks = []
# for _, row in nify_list.iterrows():
#     stocks.append(row['Symbol'])

# for stock in selected_list['stock']:
#     if stock not in stocks:
#         stocks.append(stock)

# stocks.sort()
# yaml_dict = {'stock': stocks}

# with open('StockAppApi/processes/python/testers/selected_stocks.yaml', 'w') as outfile:
#     yaml.dump(yaml_dict, outfile, default_flow_style=False)

tes = {"csv1": 'True'}

res = bool(tes.get('csv', 'False') == 'True')
print(res)
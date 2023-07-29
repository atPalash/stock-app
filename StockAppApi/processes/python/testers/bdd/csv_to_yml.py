import pandas
import yaml

csv = "StockAppApi/processes/python/testers/bdd/ind_nifty100list.csv"
df = pandas.read_csv(csv)['Symbol']
yml = yaml.dump(df.to_list())
print(yml)

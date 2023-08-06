import pandas
import yaml

csv = "StockAppApi/processes/python/testers/bdd/ind_nifty100list.csv"
df = pandas.read_csv(csv)['Symbol']
chec = df.to_list()
chec.sort()
yml = yaml.dump(chec)
print(yml)

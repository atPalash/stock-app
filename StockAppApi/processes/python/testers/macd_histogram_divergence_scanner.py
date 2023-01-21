import pandas
from StockAppApi.processes.python.system.src.command_handler import CommandHandler
from StockAppApi.base.python.src.candle_plotter import plot
from StockAppApi.base.python.src.yaml_parser import read_config

tcs = pandas.read_csv("/home/palash/dev/stock-app/StockAppApi/database/day/TCS.csv", index_col=0, parse_dates=True)
ema_query = "talibquery --ticker TCS --interval day --ohlc Close --do get --indicator ema --n 100 --latest 0"
macd_query = "talibquery --ticker TCS --interval day --ohlc Close --do get --indicator macd --n 100 --latest 0"

configFolder = "StockAppApi/configuration/"
config = read_config(configFolder + "config.yaml")

# Initialize the logger from news server
selected_stocks_yaml = configFolder + "selected_stocks.yaml"
indicator_config_yaml = configFolder + "indicator.yaml"
commandHandler = CommandHandler(selected_stocks_yaml=selected_stocks_yaml, indicator_config_yaml=indicator_config_yaml)

ema_ret = commandHandler.execute(message=ema_query, is_rest=False).obj
macd_ret = commandHandler.execute(message=macd_query, is_rest=False).obj

plot(ohlc=tcs.tail(100), ema=ema_ret['ema'], macd_histogram=macd_ret['macdhist'])

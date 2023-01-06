import glob
import pandas
import os

from StockAppApi.processes.python.talib.src.command_handler import CommandHandler
from StockAppApi.base.python.src.yaml_parser import read_config
from StockAppApi.base.python.src.server import Server
from StockAppApi.processes.python.talib.src.aggregator import Aggregator

if __name__ == "__main__":
    print("Hello Talib!")
    
    configFolder = "StockAppApi/configuration/"
    config = read_config(configFolder + "config.yaml")
    serverPort = config['port']['talib']
    masterServerPort = config['port']['master']
    
    # Initialize the logger from news server
    
    # Base::Src::Log::Init("News");
    # selected_stocks = read_config(selected_stocks_yaml)


    indicator_config_yaml = configFolder + "indicator.yaml"
    # indicator_config = read_config(indicator_config_yaml)
    aggregator = Aggregator(indicator_config_yaml)
    
    selected_stocks_yaml = configFolder + "selected_stocks.yaml"
    commandHandler = CommandHandler(selected_stocks_yaml, aggregator=aggregator)
    
    server = Server(serverPort, masterServerPort, commandHandler)
    server.register_routes()
    server.run()
    server.unregister_routes()
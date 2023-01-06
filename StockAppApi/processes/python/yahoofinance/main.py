from StockAppApi.processes.python.yahoofinance.src.command_handler import CommandHandler
from StockAppApi.base.python.src.yaml_parser import read_config
from StockAppApi.base.python.src.server import Server
from StockAppApi.processes.python.yahoofinance.src.aggregator import Aggregator

if __name__ == "__main__":
    print("Hello DataFetcher!")
    
    configFolder = "StockAppApi/configuration/"
    config = read_config(configFolder + "config.yaml")
    serverPort = config['port']['yahoofinance']
    masterServerPort = config['port']['master']
    
    # Initialize the logger from news server
    selected_stocks_yaml = configFolder + "selected_stocks.yaml"
    # Base::Src::Log::Init("News");
    # selected_stocks = read_config(selected_stocks_yaml)
    commandHandler = CommandHandler(selected_stocks_yaml)
    indicator_config_yaml = configFolder + "indicator.yaml"
    # indicator_config = read_config(indicator_config_yaml)
    aggregator = Aggregator(indicator_config_yaml, selected_stocks_yaml)
    server = Server(serverPort, masterServerPort, commandHandler)

    server.register_routes()
    server.run()
    
    aggregator.stop_schedulers()
    server.unregister_routes()
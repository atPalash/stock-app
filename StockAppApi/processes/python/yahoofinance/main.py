from StockAppApi.processes.python.yahoofinance.src.command_handler import CommandHandler
from StockAppApi.base.python.src.yaml_parser import read_config
from StockAppApi.base.python.src.server import Server

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
    server = Server(serverPort, masterServerPort, commandHandler)

    server.register_routes()
    server.run()
    server.unregister_routes()
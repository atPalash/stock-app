from processes.python.yahoofinance.src.command_handler import CommandHandler
from base.python.src.yaml_parser import read_config
from base.python.src.server import Server

if __name__ == "__main__":
    print("Hello DataFetcher!")
    
    serverPort = 8083
    masterServerPort = 8080
    
    # Initialize the logger from news server
    selected_stocks_yaml = "StockAppApi/configuration/selected_stocks.yaml"
    # Base::Src::Log::Init("News");
    selected_stocks = read_config(selected_stocks_yaml)
    commandHandler = CommandHandler(selected_stocks['stock'])
    
    server = Server(serverPort, masterServerPort, commandHandler)

    server.register_routes()
    server.run()
    server.unregister_routes()
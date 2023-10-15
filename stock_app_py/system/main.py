from stock_app_py.utility.src.yaml_parser import read_config
from stock_app_py.utility.src.server import Server
from stock_app_py.system.src.command_handler import CommandHandler

if __name__ == "__main__":
    print("Hello Systems!")

    configFolder = "/home/palash/stock-app/configuration/"
    config = read_config(configFolder + "config.yaml")
    serverPort = config["port"]["system"]
    masterServerPort = config["port"]["master"]

    # Initialize the logger from news server
    selected_stocks_yaml = configFolder + "selected_stocks.yaml"
    indicator_config_yaml = configFolder + "indicator.yaml"
    commandHandler = CommandHandler(
        selected_stocks_yaml, indicator_config_yaml=indicator_config_yaml
    )

    server = Server(serverPort, masterServerPort, commandHandler)
    server.register_routes()
    server.run()
    server.unregister_routes()

from stock_app_py.utility.src.path_helper import get_app_path
from stock_app_py.utility.src.yaml_parser import read_config
from stock_app_py.utility.src.server import Server
from stock_app_py.system.src.command_handler import CommandHandler

if __name__ == "__main__":
    print("Hello Systems!")

    config = read_config(get_app_path('config.yaml'))
    serverPort = config["port"]["system"]
    masterServerPort = config["port"]["master"]

    # Initialize the logger from news server
    selected_stocks_yaml = get_app_path('selected_stocks.yaml')
    indicator_config_yaml = get_app_path('indicator.yaml')
    commandHandler = CommandHandler(
        selected_stocks_yaml, indicator_config_yaml=indicator_config_yaml
    )

    server = Server(serverPort, masterServerPort, commandHandler)
    server.register_routes()
    server.run()
    server.unregister_routes()

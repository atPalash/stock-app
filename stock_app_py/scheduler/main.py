from stock_app_py.scheduler.src.command_handler import CommandHandler
from stock_app_py.utility.src.yaml_parser import read_config
from stock_app_py.utility.src.server import Server

if __name__ == "__main__":
    print("Hello Scheduler!")

    configFolder = "/home/palash/stock-app/configuration/"
    config = read_config(configFolder + "config.yaml")
    serverPort = config["port"]["scheduler"]
    masterServerPort = config["port"]["master"]

    indicator_config_yaml = configFolder + "indicator.yaml"
    selected_stocks_yaml = configFolder + "selected_stocks.yaml"

    command_handler = CommandHandler(
        indicator_config_file=indicator_config_yaml,
        selected_stocks_config_file=selected_stocks_yaml,
        master_url=f"http://localhost:{masterServerPort}",
    )

    server = Server(serverPort, masterServerPort, command_handler)
    server.register_routes()
    server.run()
    server.unregister_routes()

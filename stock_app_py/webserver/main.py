import os

from stock_app_py.utility.src.yaml_parser import read_config
from stock_app_py.webserver.src.webserver import Webserver

if __name__ == "__main__":
    print("Hello webserver!")

    configFolder = "/home/palash/stock-app/configuration/"
    config = read_config(configFolder + "config.yaml")
    serverPort = config["port"]["webserver"]
    masterServerPort = config["port"]["master"]

    indicator_config_yaml = configFolder + "indicator.yaml"
    selected_stocks_yaml = configFolder + "selected_stocks.yaml"

    server = Webserver(
        port=serverPort,
        master_server_port=masterServerPort,
        indicator_config_file=indicator_config_yaml,
        selected_stocks_config_file=selected_stocks_yaml,
    )
    server.register_routes()
    server.run(debug=False)
    server.unregister_routes()

import os

from StockAppApi.base.python.src.yaml_parser import read_config
from StockAppApi.processes.python.webserver.src.webserver import Webserver

if __name__ == "__main__":
    print("Hello webserver!")

    configFolder = "StockAppApi/configuration/"
    config = read_config(configFolder + "config.yaml")
    serverPort = config['port']['webserver']
    masterServerPort = config['port']['master']

    indicator_config_yaml = configFolder + "indicator.yaml"
    selected_stocks_yaml = configFolder + "selected_stocks.yaml"

    server = Webserver(port=serverPort,
                       master_server_port=masterServerPort,
                       indicator_config_file=indicator_config_yaml,
                       selected_stocks_config_file=selected_stocks_yaml)
    server.register_routes()
    server.run(debug=False)
    server.unregister_routes()

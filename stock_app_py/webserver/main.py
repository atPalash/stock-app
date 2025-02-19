from stock_app_py.utility.src.path_helper import get_app_path

from stock_app_py.utility.src.yaml_parser import read_config
from stock_app_py.webserver.src.webserver import Webserver

if __name__ == "__main__":
    print("Hello webserver!")

    config = read_config(get_app_path("config.yaml"))
    serverPort = config["port"]["webserver"]
    masterServerPort = config["port"]["master"]

    indicator_config_yaml = get_app_path("indicator.yaml")
    selected_stocks_yaml = get_app_path("selected_stocks.yaml")

    server = Webserver(
        port=serverPort,
        master_server_port=masterServerPort,
        indicator_config_file=indicator_config_yaml,
        selected_stocks_config_file=selected_stocks_yaml,
    )
    server.register_routes()
    server.run(debug=False)
    server.unregister_routes()

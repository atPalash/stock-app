from stock_app_py.scheduler.src.command_handler import CommandHandler
from stock_app_py.utility.src.path_helper import get_app_path
from stock_app_py.utility.src.yaml_parser import read_config
from stock_app_py.utility.src.server import Server

if __name__ == "__main__":
    print("Hello Scheduler!")

    config = read_config(get_app_path('config.yaml'))
    serverPort = config["port"]["scheduler"]
    masterServerPort = config["port"]["master"]

    indicator_config_yaml = get_app_path('indicator.yaml')
    selected_stocks_yaml = get_app_path('selected_stocks.yaml')

    command_handler = CommandHandler(
        indicator_config_file=indicator_config_yaml,
        selected_stocks_config_file=selected_stocks_yaml,
        master_url=f"http://localhost:{masterServerPort}",
    )

    server = Server(serverPort, masterServerPort, command_handler)
    server.register_routes()
    server.run()
    server.unregister_routes()

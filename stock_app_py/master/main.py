import os
from flask import render_template, request, Flask
import requests

from src.command_handler import CommandHandler
from stock_app_py.utility.src.path_helper import get_app_path
from stock_app_py.utility.src.yaml_parser import read_config
from stock_app_py.utility.src.server import Server
from stock_app_py.interface.commandHandlerIf import CommandHandlerIf


class ServerExt(Server):
    def __init__(
        self, port: int, master_server_port: int, command_handler: CommandHandlerIf
    ) -> None:
        super().__init__(port, master_server_port, command_handler)
        self.app = Flask(
            __name__,
            static_folder="../../../static",
            template_folder="../../../templates",
        )

        @self.app.route("/", methods=["GET", "POST"])
        def base_api():
            return self.handle_request(request)

            # TODO check below for docker implementation
            # if request.method == "GET":
            #     # # TODO
            #     # # Get the URL to proxy from the query parameter
            #     # url = 'http://localhost:8085'
            #     # if not url:
            #     #     return 'No URL provided'

            #     # # Forward the request to the child server and get the HTML response
            #     # response = requests.get(url)

            #     # # Return the HTML response to the client
            #     # return response.text
            #     return self.handle_request(request)
            # else:

        @self.app.route("/html", methods=["GET", "POST"])
        def html():
            url = "http://localhost:8087"
            response = requests.get(url)
            return response.text


if __name__ == "__main__":
    print("Hello Master!")

    config = read_config(get_app_path('config.yaml'))
    serverPort = config["port"]["master"]

    indicator_config_yaml = get_app_path('indicator.yaml')
    selected_stocks_yaml = get_app_path('selected_stocks.yaml')

    command_handler = CommandHandler()

    server = ServerExt(serverPort, -1, command_handler)
    server.run()

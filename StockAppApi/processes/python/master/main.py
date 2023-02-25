import os
from flask import render_template, request, Flask
import requests

from src.command_handler import CommandHandler
from StockAppApi.base.python.src.yaml_parser import read_config
from StockAppApi.base.python.src.server import Server
from StockAppApi.base.python.interface.commandHandlerIf import CommandHandlerIf


class ServerExt(Server):
    def __init__(self, port: int, master_server_port: int, command_handler: CommandHandlerIf) -> None:
        super().__init__(port, master_server_port, command_handler)
        self.app = Flask(__name__)

        @self.app.route("/", methods=['GET', 'POST'])
        def base_api():
            if request.method == "GET":
                # # TODO
                # # Get the URL to proxy from the query parameter
                # url = 'http://localhost:8085'
                # if not url:
                #     return 'No URL provided'

                # # Forward the request to the child server and get the HTML response
                # response = requests.get(url)

                # # Return the HTML response to the client
                # return response.text
                return self.handle_request(request)
            else:
                return self.handle_request(request)


if __name__ == "__main__":
    print("Hello Master!")

    configFolder = "StockAppApi/configuration/"
    config = read_config(configFolder + "config.yaml")
    serverPort = config['port']['master']

    indicator_config_yaml = configFolder + "indicator.yaml"
    selected_stocks_yaml = configFolder + "selected_stocks.yaml"

    command_handler = CommandHandler()

    server = ServerExt(serverPort, -1, command_handler)
    server.run()

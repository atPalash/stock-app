import os
from flask import render_template, request, Flask
import requests

from StockAppApi.processes.python.scheduler.src.command_handler import CommandHandler
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
                def getAllplots(interval:str) -> str:
                    path = "StockAppApi/processes/python/scheduler/static/plot"
                    onlyfiles = ""
                    for f in os.listdir(path):
                        if os.path.isfile(os.path.join(path, f)):
                            onlyfiles+=f'{f},'
                    return onlyfiles 
                plots = getAllplots('day')
                return render_template('index.html', plots=plots)
            else:
                return self.handle_request(request)
            
if __name__ == "__main__":
        print("Hello Scheduler!")
        
        configFolder = "StockAppApi/configuration/"
        config = read_config(configFolder + "config.yaml")
        serverPort = config['port']['scheduler']
        masterServerPort = config['port']['master']
        
        indicator_config_yaml = configFolder + "indicator.yaml"   
        selected_stocks_yaml = configFolder + "selected_stocks.yaml"

        command_handler = CommandHandler(indicator_config_file=indicator_config_yaml, 
        selected_stocks_config_file=selected_stocks_yaml, master_url=f"http://localhost:{masterServerPort}")
        
        server = ServerExt(serverPort, masterServerPort, command_handler)
        server.register_routes()
        server.run()
        server.unregister_routes()


# from flask import Flask, render_template
# import os

# app = Flask(__name__)

# @app.route('/')
# def home():
#     def getAllplots(interval:str) -> str:
#         path = "StockAppApi/processes/python/testers/static/plot"
#         onlyfiles = ""
#         for f in os.listdir(path):
#             if os.path.isfile(os.path.join(path, f)):
#                 onlyfiles+=f'{f},'
#         return onlyfiles 
#     plots = getAllplots('day')
#     return render_template('index.html', plots=plots)

# if __name__ == '__main__':
#     app.run(port=8001)
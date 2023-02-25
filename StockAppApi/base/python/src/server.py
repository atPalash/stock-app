from StockAppApi.base.python.interface.serverIf import ServerIf
from StockAppApi.base.python.interface.commandHandlerIf import CommandHandlerIf
from flask import Flask, request
import requests

class Server(ServerIf):
    def __init__(self, port:int, master_server_port:int, command_handler: CommandHandlerIf) -> None:
        super().__init__()
        self.app = Flask(__name__)
        self.port = port
        self.master_server_port = master_server_port
        self.command_handler = command_handler
        
        @self.app.route('/', methods=['GET', 'POST'])
        def base_api():
            self.handle_request(request)

    
    def handle_request(self,req:request):
        if request.method == 'POST':
            try:
                print("POSTED", request.data)
                result = self.command_handler.execute(request.data.decode(), is_rest=True)
                return result.response, result.errorCode
            except Exception as e:
                return result.exceptionStr, result.errorCode
        else:
            # Handle GET request
            return f'Hello, {__name__}'
            
    def run(self):
        # For production server
        # from waitress import serve
        # serve(self.app, host='localhost', port=self.port)
        self.app.run(host='localhost', port=self.port)

    def register_routes(self):
        try:
            registrationMessage = f'register --port {self.port} --query {self.command_handler.get_command_as_str()}'
            master_url = f'http://localhost:{self.master_server_port}'
            res = requests.post(master_url, data=registrationMessage)
            # log registration
        except Exception as e:
            # log registration exception
            print(e.args)
            
    def unregister_routes(self):
        try:
            unRegistrationMessage = f'unregister --port {self.port} --query {self.command_handler.get_command_as_str()}'
            master_url = f'localhost:{self.master_server_port}'
            res = requests.post(master_url, data=unRegistrationMessage)
            # log registration
        except Exception as e:
            # log registration exception
            print(e.args)
        
if __name__ == "__main__":
    server = Server(8083, -1, None)
    server.run()
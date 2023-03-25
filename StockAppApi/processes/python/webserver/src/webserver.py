from flask import render_template, request, Flask

from StockAppApi.base.python.src.message_parser import parse_message
from StockAppApi.processes.python.system.src.command_handler import CommandHandler
from StockAppApi.base.python.src.server import Server

class Webserver(Server):
    def __init__(self, port: int, master_server_port: int, indicator_config_file:str, selected_stocks_config_file:str) -> None:
        super().__init__(port, master_server_port, None)
        self.app = Flask(__name__, static_folder="../../../../static", template_folder="../../../../templates")
        self.system_command_handler = CommandHandler(indicator_config_yaml=indicator_config_file,
                                                     selected_stocks_yaml=selected_stocks_config_file)

        @self.app.route("/", methods=['GET', 'POST'])
        def base_api():
            if request.method == "GET":
                return render_template('index.html')
            else:
                return self.handle_request(request)
        
        @self.app.route("/ohlc", methods=['POST'])
        def ohlc_api():
            return self.handle_request(req=request)
            
    def handle_request(self, req: request):
        if request.method == 'POST':
            try:
                result = self.system_command_handler.execute(
                        request.json['query'], is_rest=True)
                return result.response, result.errorCode
            except Exception as e:
                return result.exceptionStr, result.errorCode
        else:
            # Handle GET request
            return f'Hello, {__name__}'
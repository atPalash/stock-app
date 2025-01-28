from flask import jsonify, render_template, request, Flask
import json
from flask_cors import CORS

from stock_app_py.system.src.command_handler import CommandHandler
from stock_app_py.utility.src.path_helper import get_app_path
from stock_app_py.utility.src.server import Server


class Webserver(Server):
    def __init__(
        self,
        port: int,
        master_server_port: int,
        indicator_config_file: str,
        selected_stocks_config_file: str,
    ) -> None:
        super().__init__(port, master_server_port, None)
        self.app = Flask(
            __name__,
            static_folder=get_app_path("static"),
            template_folder=get_app_path("templates"),
        )
        CORS(self.app)
        self.system_command_handler = CommandHandler(
            indicator_config_yaml=indicator_config_file,
            selected_stocks_yaml=selected_stocks_config_file,
        )

        @self.app.route("/", methods=["GET", "POST"])
        def base_api():
            if request.method == "GET":
                return render_template("index.html")
            else:
                return self.handle_request(request)

        @self.app.route("/ohlc", methods=["POST"])
        def ohlc_api():
            return self.handle_request(req=request)

        @self.app.route("/macd-hist-scanner", methods=["POST"])
        def macd_hist_scanner_api():
            return self.handle_request(req=request)

        @self.app.route("/stage2-scanner", methods=["POST"])
        def stage2_scanner_api():
            return self.handle_request(req=request)

        @self.app.route("/config", methods=["GET", "POST"])
        def config():
            return self.config(req=request)

        @self.app.route("/gherkin-query", methods=["GET", "POST"])
        def gherkin_query():
            return self.handle_request(req=request)

        @self.app.route("/financials-query", methods=["GET", "POST"])
        def financials_query():
            return self.handle_request(req=request)

        @self.app.route("/statements", methods=["GET", "POST"])
        def statements_query():
            return self.handle_request(req=request)

        @self.app.route("/user-config", methods=["GET", "POST"])
        def user_config():
            return self.handle_request(req=request)

        @self.app.route("/user-login", methods=["GET", "POST"])
        def user_login():
            return self.handle_request(req=request)

        @self.app.route("/indicators", methods=["GET", "POST"])
        def indicators_query():
            return self.handle_request(req=request)

        @self.app.route("/ticker-event", methods=["GET", "POST"])
        def ticker_event():
            return self.handle_request(req=request)

        @self.app.route("/options", methods=["GET", "POST"])
        def options():
            return self.handle_request(req=request)

    def handle_request(self, req: request):
        if request.method == "POST":
            try:
                result = self.system_command_handler.execute(
                    request.json["query"], is_rest=True
                )
                return result.response, result.errorCode
            except Exception as e:
                return result.exceptionStr, result.errorCode
        else:
            # Handle GET request
            return f"Hello, {__name__}"

    def config(self, req: request):
        user_config = get_app_path("user_config.json")
        if request.path == "/save-layout":
            if request.method == "POST":
                try:
                    # Open a file for writing
                    with open(user_config, "r+") as f:
                        config = json.load(f)
                        layout_id = next(iter(req.json))
                        config["react"][layout_id] = req.json[layout_id]
                        json.dump(config, f, indent=4)
                    return jsonify("Ok"), 200
                except Exception as e:
                    return e.args, 400
            elif request.method == "GET":
                try:
                    with open(user_config, "r") as f:
                        # Read file
                        data = f.read()
                    config = json.loads(data)
                    return jsonify(config["react"]), 200
                except Exception as e:
                    return jsonify("Error"), 400
        else:
            # TODO fix DRY here, the entire html part will be replaced by react
            if request.method == "POST":
                try:
                    # Open a file for writing
                    with open(user_config, "w") as f:
                        # Write the JSON data to the file
                        json.dump(req.json, f)
                    return jsonify("Ok"), 200
                except Exception as e:
                    return e.args, 400
            elif request.method == "GET":
                try:
                    with open(user_config, "r") as f:
                        # Write the JSON data to the file
                        return jsonify(f.read()), 200
                except:
                    return jsonify("Error"), 400

from stock_app_py.interface.serverIf import ServerIf
from stock_app_py.interface.commandHandlerIf import CommandHandlerIf
from flask import Flask, request
import requests
import subprocess


class Server(ServerIf):
    def __init__(
        self, port: int, master_server_port: int, command_handler: CommandHandlerIf
    ) -> None:
        super().__init__()
        self.app = Flask(__name__)
        self.port = port
        self.master_server_port = master_server_port
        self.command_handler = command_handler
        self.ip_address = ""
        self.get_ip_address()

        @self.app.route("/", methods=["GET", "POST"])
        def base_api():
            return self.handle_request(request)

    def handle_request(self, req: request):
        if request.method == "POST":
            try:
                result = self.command_handler.execute(
                    request.data.decode(), is_rest=True
                )
                return result.response, result.errorCode
            except Exception as e:
                return result.exceptionStr, result.errorCode
        else:
            # Handle GET request
            return f"Hello, {__name__}"

    def run(self, debug=False):
        # For production server
        # from waitress import serve
        # serve(self.app, host='localhost', port=self.port)
        self.app.run(host="0.0.0.0", port=self.port, debug=debug)

    def register_routes(self):
        try:
            registrationMessage = f"register --host {self.ip_address} --port {self.port} --query {self.command_handler.get_command_as_str()}"
            master_url = f"http://localhost:{self.master_server_port}"
            if Server.__is_running_in_container():
                master_url = f"http://master:{self.master_server_port}"
            res = requests.post(master_url, data=registrationMessage)
            # log registration
        except Exception as e:
            # log registration exception
            print(e.args)

    def unregister_routes(self):
        try:
            unRegistrationMessage = f"unregister --port {self.port} --query {self.command_handler.get_command_as_str()}"
            master_url = f"http://localhost:{self.master_server_port}"
            if Server.__is_running_in_container():
                master_url = f"http://master:{self.master_server_port}"
            res = requests.post(master_url, data=unRegistrationMessage)
            # log registration
        except Exception as e:
            # log registration exception
            print(e.args)

    def get_ip_address(self):
        if self.ip_address == "":
            # Execute ifconfig command to get network interface information
            result = subprocess.run(
                ["ifconfig", "eth0"], capture_output=True, text=True
            )

            # Parse the output to extract the IP address
            ip_address = None
            for line in result.stdout.split("\n"):
                if "inet " in line:
                    ip_address = line.split()[1]
                    break

            print(f"IP Address: {ip_address}")
            self.ip_address = ip_address
        return self.ip_address

    @staticmethod
    def __is_running_in_container():
        """
        Returns True if the current code is running in a container, False otherwise.
        """
        with open("/proc/1/cgroup", "r") as f:
            for line in f:
                if "docker" in line or "kube" in line:
                    return True
        return False


if __name__ == "__main__":
    server = Server(8083, -1, None)
    server.run()

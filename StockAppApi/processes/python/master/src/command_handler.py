from StockAppApi.base.python.interface.commandHandlerIf import CommandHandlerIf, Response, get_commands_as_str
from StockAppApi.base.python.src.message_parser import parse_message
import requests

class CommandHandler(CommandHandlerIf):
    def __init__(self) -> None:
        super().__init__()
        self.registered_commands = {}
        
    def execute(self, message: str, is_rest=False):
        try:
            arguments = parse_message(message=message) # there will be no sub-command

            if arguments['command'] == "register":
                commands = arguments['query'].split(",")
                for query in commands:
                    query = query.replace(" ", "").replace("\t", "")
                    self.registered_commands[query] = arguments["port"]
                return Response("Registered", 200, "", True)
            elif arguments['command'] == "unregister":
                for command, port in self.registered_commands.items():
                    if port == arguments['port']:
                        del self.registered_commands[command]
                return Response("Unregistered", 200, "", True)
            elif arguments['command'] in self.registered_commands:
                url = "http://localhost:" + self.registered_commands[arguments["command"]]
                res = requests.post(url, message)
                return Response(res.text, 200, "", True)
            else:
                return Response("Command not allowed", 500, "check the commands", False)         
        except Exception as e:
            if is_rest:
                return Response("exception", 400, e.args, False)

    def get_command_as_str(self) -> str:
        """Register the commands associated with this command handler to master
        server.

        Returns:
            str: list of supported commands
        """
        return get_commands_as_str(self.commands)

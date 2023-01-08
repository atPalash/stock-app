class Response:
    def __init__(self, response="", errorCode=200, exceptionStr="", ok=True) -> None:
        self.response = response
        self.errorCode = errorCode
        self.exceptionStr = exceptionStr
        self.ok = ok

def get_commands_as_str(commands_dict: dict)-> str:
    commands = ""
    for key in commands_dict.keys():
        commands += key + ',' 
    return commands

class CommandHandlerIf:
    def execute(self, message:str, is_rest=True) -> Response:
        pass
    def get_command_as_str(self) -> str:
        pass
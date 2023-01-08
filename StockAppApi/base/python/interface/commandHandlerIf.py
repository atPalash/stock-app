class Response:
    def __init__(self, response="", errorCode=200, exceptionStr="", ok=True) -> None:
        self.response = response
        self.errorCode = errorCode
        self.exceptionStr = exceptionStr
        self.ok = ok
        
class CommandHandlerIf:
    def execute(self, message:str, is_rest=True) -> Response:
        pass
    def get_command_as_str(self) -> str:
        pass
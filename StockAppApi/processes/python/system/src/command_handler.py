from StockAppApi.base.python.interface.commandHandlerIf import CommandHandlerIf, Response
from StockAppApi.base.python.src.message_parser import parse_message
from StockAppApi.base.python.src.yaml_parser import read_config
from StockAppApi.processes.python.system.src.elder_impulse import ElderImpulse

class CommandHandler(CommandHandlerIf):
    def __init__(self, selected_stocks_yaml, indicator_config_yaml) -> None:
        super().__init__()
        self.commands = { "elder" : ElderImpulse }
        self.selected_stocks_yaml = selected_stocks_yaml
        self.indicator_config_yaml = indicator_config_yaml
        
    def execute(self, message: str, is_rest=True) -> Response:
        try:
            arguments = parse_message(message=message)[0] # there will be no sub-command
            system = self.commands[arguments['command']](self.indicator_config_yaml, 
                                                         self.selected_stocks_yaml, message) # the message contains the parameters
            res = system.execute()
            
            if is_rest:
                # for rest calls we return Response object
                if res['status']:
                    return Response(str(res['result']), 200, "", True)
                else:
                    return Response("", 405, "MethodNotAllowed", False)
            
            return res           
            
        except Exception as e:
            # Base::Src::Log::LogCritical(__FILE__, __LINE__, e.what());
            return Response("exception", 400, e.args, False)

    def get_command_as_str(self) -> str:
        commands = ""
        for key in self.commands.keys():
            commands += key + ',' 
        return commands

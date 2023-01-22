from StockAppApi.base.python.interface.commandHandlerIf import CommandHandlerIf, Response, get_commands_as_str
from StockAppApi.base.python.src.message_parser import parse_message
from StockAppApi.processes.python.scheduler.interface.scheduler_if import SchedulerIf

class CommandHandler(CommandHandlerIf):
    def __init__(self, system_scheduler:SchedulerIf, yahoo_scheduler:SchedulerIf) -> None:
        super().__init__()
        self.commands = {
            "start": self.__start,
            "stop": self.__stop
        }
        self.system_scheduler = system_scheduler
        self.yahoo_scheduler = yahoo_scheduler
        
    def execute(self, message: str) -> Response:
        try:
            command = parse_message(message=message)
            self.commands[command['command']]()
            return Response("Stopped schedulers", 200, "", True)
        except Exception as e:
            # Base::Src::Log::LogCritical(__FILE__, __LINE__, e.what());
            return Response("exception", 400, e.args, False)

    def get_command_as_str(self) -> str:
        return get_commands_as_str(self.commands)
    
    def __start(self):
        self.system_scheduler.run()
        self.yahoo_scheduler.run()
    
    def __stop(self):
        self.system_scheduler.stop()
        self.yahoo_scheduler.stop()
        


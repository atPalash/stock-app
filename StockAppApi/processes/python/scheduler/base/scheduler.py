from StockAppApi.processes.python.scheduler.interface.scheduler_if import SchedulerIf

class Scheduler(SchedulerIf):
    def __init__(self, indicator_config_file: str, selected_stocks_config_file:str, master_url) -> None:
        self.indicator_config_file = indicator_config_file
        self.selected_stocks_config_file = selected_stocks_config_file
        self.master_url = master_url
        self.schedulers = {}
        
    def run():
        pass
    
    def stop():
        pass
    
    def notify():
        pass
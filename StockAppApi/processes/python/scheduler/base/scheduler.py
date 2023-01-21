from StockAppApi.processes.python.scheduler.interface.scheduler_if import SchedulerIf
from StockAppApi.base.python.src.yaml_parser import read_config
class Scheduler(SchedulerIf):
    def __init__(self, indicator_config_file: str, selected_stocks_config_file:str, master_url) -> None:
        self.indicator_config = read_config(indicator_config_file)
        self.selected_stocks_config = read_config(selected_stocks_config_file)
        self.master_url = master_url
        self.schedulers = {}
        
    def run():
        pass
    
    def stop(self):
        for _, scheduler in self.schedulers.items():
            scheduler.shutdown(wait=False)
    
    def notify():
        pass
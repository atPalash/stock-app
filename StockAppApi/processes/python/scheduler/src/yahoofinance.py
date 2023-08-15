from apscheduler.schedulers.background import BackgroundScheduler
import pytz

from StockAppApi.processes.python.scheduler.base.scheduler import Scheduler
from StockAppApi.processes.python.system.src.command_handler import CommandHandler

class YahooScheduler(Scheduler):
    def __init__(self, indicator_config_file: str, selected_stocks_config_file:str, master_url:str) -> None:
        super().__init__(indicator_config_file=indicator_config_file, 
                         selected_stocks_config_file=selected_stocks_config_file, 
                         master_url=master_url)
        self.schedulers = {}

        self.system_command_handler = CommandHandler(indicator_config_yaml=indicator_config_file,
                                                     selected_stocks_yaml=selected_stocks_config_file)

    def run(self):
        scheduler = BackgroundScheduler()
        for interval in self.indicator_config['indicator']['data']:
            self.__periodic_download(interval=interval)
            if interval == 'week':
                scheduler.add_job(self.__periodic_download, 'cron', hour='17',
                                  day_of_week='fri', timezone=pytz.timezone('Asia/Kolkata'), args=[interval])
            elif interval == 'day':
                scheduler.add_job(self.__periodic_download, 'cron', hour='16',
                                  day_of_week='mon-fri', timezone=pytz.timezone('Asia/Kolkata'), args=[interval])
            elif interval == 'hour':
                scheduler.add_job(self.__periodic_download, 'cron', hour='9-16', minute='16',
                                  day_of_week='mon-fri', timezone=pytz.timezone('Asia/Kolkata'), args=[interval])
            else:
                print(f"Error: This {interval} is not allowed")
            self.schedulers[interval] = scheduler
        
        scheduler.add_job(self.__monthly_fundamental_download, 'cron', day='1', hour='1', 
            timezone=pytz.timezone('Asia/Kolkata'))
        scheduler.start()

    def __periodic_download(self, interval: str):
        """Analysis method will include all the possible combination of the indicators.
        Donot call this method directly to avoid confusion, use the above methods. 

        Args:
            interval (str): _description_
            add_latest (bool, optional): _description_. Defaults to False.
        """
        try:
            query = f"yahoofinance --ticker all --interval {interval} --do get --pandas 0  --csv 1"
            ret = self.system_command_handler.execute(message=query, is_rest=False) # just download the data, only print the errors
            if ret.errors != "":
                print("ERROR yahoo system", ret.errors)
        except Exception as e:
            print("ERROR __periodic_download", e.args)
        
    def __monthly_fundamental_download(self):
        try:
            query = f"yahoofinance --ticker all --do fundamentals --pandas 0  --csv 1"
            ret = self.system_command_handler.execute(message=query, is_rest=False) # just download the data, only print the errors
            if ret.errors != "":
                print("ERROR yahoo fundamental download system", ret.errors) # TODO
        except Exception as e:
            print("ERROR __monthly_fundamental_download", e.args)


if __name__ == "__main__":
    from StockAppApi.base.python.src.yaml_parser import read_config
    configFolder = "StockAppApi/configuration/"
    config = read_config(configFolder + "config.yaml")
    indicator_config_yaml = configFolder + "indicator.yaml"   
    selected_stocks_yaml = configFolder + "selected_stocks.yaml"
    scheduler = YahooScheduler(indicator_config_yaml, selected_stocks_yaml, "dummy")
    scheduler.run()

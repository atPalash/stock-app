import requests
import pytz
from apscheduler.schedulers.background import BackgroundScheduler

from StockAppApi.processes.python.scheduler.base.scheduler import Scheduler
from StockAppApi.processes.python.system.src.command_handler import CommandHandler

class SystemScheduler(Scheduler):
    def __init__(self, indicator_config_file: str, selected_stocks_config_file:str, master_url:str) -> None:
        super().__init__(indicator_config_file=indicator_config_file, 
                         selected_stocks_config_file=selected_stocks_config_file, 
                         master_url=master_url)
        self.schedulers.update({
            "hourly_system": self.__hourly_systems
        })

    def stop(self):
        for _, scheduler in self.schedulers.items():
            scheduler.shutdown(wait=False)

    def run(self):
        scheduler = BackgroundScheduler()
        scheduler.add_job(self.__hourly_systems, 'cron', hour='9-17', minute='20',
                        day_of_week='mon-fri', timezone=pytz.timezone('Asia/Kolkata'), 
                        args=[])
        
        self.schedulers[self.__hourly_systems.__name__] = scheduler

    def __hourly_systems(self):
        """Build the elder impulse system logic, tag each stock with the actions
        allow, filtering options based on action.
        """
        try:
            parameter_string = "elder --ema_window 13 --ema_n 100 --macd_fast_period 13 macd_slow_period 26 macd_signal_period 9 --macdhist_n 20"
            
            command_handler = CommandHandler(indicator_config_yaml=self.indicator_config_file,
                                            selected_stocks_yaml=self.selected_stocks_config_file)
            res = command_handler.execute(message=parameter_string, is_rest=False)
            message= f"sendEmbed --channel general "
            
            if res['status']:
                df = res['result']
                bull = df.query('trend=="bullish"').to_string()
                requests.post(self.master_url, data=message + f"--title Bulls --message {bull}")
                
                bear = df.query('trend=="bearish"').to_string()
                requests.post(self.master_url, data=message + f"--title Bears --message {bear}")
                
                no_trend = df.query('trend=="no trend"').to_string()
                requests.post(self.master_url, data=message + f"--title NoTrend --message {no_trend}")
            else:
                requests.post(self.master_url, data=f"Error:{__file__}")
        except Exception as e:
            requests.post(self.master_url, data=f"{e.args}")
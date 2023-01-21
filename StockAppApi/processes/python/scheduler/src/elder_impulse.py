import requests
import pytz
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import pandas

from StockAppApi.processes.python.scheduler.base.scheduler import Scheduler
from StockAppApi.processes.python.system.src.command_handler import CommandHandler

class ElderImpulseScheduler(Scheduler):
    def __init__(self, indicator_config_file: str, selected_stocks_config_file:str, master_url:str) -> None:
        super().__init__(indicator_config_file=indicator_config_file, 
                         selected_stocks_config_file=selected_stocks_config_file, 
                         master_url=master_url)
        self.indicator_config_file = indicator_config_file
        self.selected_stocks_config_file = selected_stocks_config_file
        self.schedulers = {}
        self.timezone = pytz.timezone('Asia/Kolkata')
        self.elder_impulse_df = None

    def run(self):
        scheduler = BackgroundScheduler()
        scheduler.add_job(self.__hourly_elder_impulse, 'cron', hour='9-16', minute='17',
                        day_of_week='mon-fri', timezone=self.timezone, 
                        args=[])
        self.schedulers[self.__hourly_elder_impulse.__name__] = scheduler
        scheduler.start()

    def __hourly_elder_impulse(self):
        """The hourly Elder impulse system call
        """
        try:
            parameter_string = "elderimpulse --window 13 --n 100 --macd_fast_period 13 macd_slow_period 26 macd_signal_period 9"
            
            command_handler = CommandHandler(indicator_config_yaml=self.indicator_config_file,
                                            selected_stocks_yaml=self.selected_stocks_config_file)
            res = command_handler.execute(message=parameter_string, is_rest=False)
            message= f"sendEmbed --channel general "
            
            if self.elder_impulse_df is not None:
                # Compare the columns and get the rows that are different
                diff_rows = pandas.concat([res.obj['trend'], self.elder_impulse_df['trend']]).drop_duplicates(keep=False)
                if not diff_rows.empty:
                    requests.post(self.master_url, data=message + f"--title ElderImpulse --message {diff_rows.to_string()}")
                else:
                    requests.post(self.master_url, data=message + f"--title ElderImpulse --message No update in elder impulse")
                
            self.elder_impulse_df = res.obj
            
            # Send the list of selected stocks trend at start of day
            now_in_kolata = datetime.datetime.now(self.timezone)
            target_time = datetime.time(hour=9, minute=0, second=0)
            if now_in_kolata.time() < target_time:
                if res.obj is not None:
                    df = self.elder_impulse_df.to_string(max_rows=None, max_cols=None, index=False)
                    requests.post(self.master_url, data=message + f"--title ElderImpulse --message {df}")
                else:
                    requests.post(self.master_url, data=f"Error:{__file__}")  
            
        except Exception as e:
            requests.post(self.master_url, data=f"{e.args}")
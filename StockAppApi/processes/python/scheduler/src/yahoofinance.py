from apscheduler.schedulers.background import BackgroundScheduler
import pytz
from datetime import datetime

from StockAppApi.processes.python.yahoofinance.src.data_fetcher import download_historical_data
from StockAppApi.base.python.src.yaml_parser import read_config
from StockAppApi.processes.python.scheduler.base.scheduler import Scheduler


class YahooScheduler(Scheduler):
    def __init__(self, indicator_config_file: str, selected_stocks_config_file:str, master_url:str) -> None:
        super().__init__(indicator_config_file=indicator_config_file, 
                         selected_stocks_config_file=selected_stocks_config_file, 
                         master_url=master_url)
        self.schedulers = {}

    def run(self):
        for interval in read_config(self.indicator_config_file)['indicator']['data']:
            scheduler = BackgroundScheduler()
            if interval == 'week':
                scheduler.add_job(self.__periodic_download, 'cron', hour='16',
                                  day_of_week='fri', timezone=pytz.timezone('Asia/Kolkata'), args=[interval])
                scheduler.start()
            elif interval == 'day':
                scheduler.add_job(self.__periodic_download, 'cron', hour='16',
                                  day_of_week='mon-fri', timezone=pytz.timezone('Asia/Kolkata'), args=[interval])
                scheduler.start()
            elif interval == 'hour':
                scheduler.add_job(self.__periodic_download, 'cron', hour='9-16', minute='16',
                                  day_of_week='mon-fri', timezone=pytz.timezone('Asia/Kolkata'), args=[interval])
                scheduler.start()
            else:
                print(f"Error: This {interval} is not allowed")

            self.schedulers[interval] = scheduler

    def __periodic_download(self, interval: str):
        """Analysis method will include all the possible combination of the indicators.
        Donot call this method directly to avoid confusion, use the above methods. 

        Args:
            interval (str): _description_
            add_latest (bool, optional): _description_. Defaults to False.
        """
        destinations_ = {'1d': 'day', '1h': 'hour', '1wk': 'week'}
        intervals_ = {'day': '1d', 'hour': '1h', 'week': '1wk'}
        periods_ = {'1d': '5y', '1h': '2y', '1wk': 'max'} # if max is not set then the empty dataframe is returned by yahoo, for dataframe of stocks of different size
        indicator_config = read_config(
            self.indicator_indicator_config_file)['indicator']
        selected_stocks = read_config(self.selected_stocks_yaml)

        tickers = [tick + '.NS' for tick in selected_stocks['stock']]
        yahoo_interval = intervals_[interval]
        download_historical_data(tickers=tickers,
                                 period=periods_[interval], 
                                 interval=yahoo_interval,
                                 as_csv=True,
                                 destination=f'StockAppApi/database/{destinations_[yahoo_interval]}')

        # Get the timezone object for the desired time zone
        tz = pytz.timezone("Asia/Kolkata")

        # Get the current time in the specified time zone
        now = datetime.now(tz)

        # Print the current time in the specified time zone
        now = now.strftime("%Y-%m-%d %H:%M:%S %Z")
        print(f"[{now}] Downloaded {interval} data")
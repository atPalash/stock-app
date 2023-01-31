from apscheduler.schedulers.background import BackgroundScheduler
import pytz
from datetime import datetime

from StockAppApi.processes.python.yahoofinance.src.data_fetcher import download_historical_data, download_stock_stats
from StockAppApi.processes.python.scheduler.base.scheduler import Scheduler


class YahooScheduler(Scheduler):
    def __init__(self, indicator_config_file: str, selected_stocks_config_file:str, master_url:str) -> None:
        super().__init__(indicator_config_file=indicator_config_file, 
                         selected_stocks_config_file=selected_stocks_config_file, 
                         master_url=master_url)
        self.schedulers = {}

    def run(self):
        scheduler = BackgroundScheduler()
        for interval in self.indicator_config['indicator']['data']:
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
        
        # scheduler.add_job(self.__monthly_fundamental_download, 'cron', day='1', hour='1', 
        #     timezone=pytz.timezone('Asia/Kolkata'))
        # self.__monthly_fundamental_download()
        scheduler.start()

    def __periodic_download(self, interval: str):
        """Analysis method will include all the possible combination of the indicators.
        Donot call this method directly to avoid confusion, use the above methods. 

        Args:
            interval (str): _description_
            add_latest (bool, optional): _description_. Defaults to False.
        """
        intervals_ = {'day': '1d', 'hour': '1h', 'week': '1wk'}
        periods_ = {'day': '5y', 'hour': '2y', 'week': '10y'}
        
        selected_stocks = self.selected_stocks_config
        tickers = [tick + '.NS' for tick in selected_stocks['stock']]
        yahoo_interval = intervals_[interval]
        download_historical_data(tickers=tickers,
                                 period=periods_[interval], 
                                 interval=yahoo_interval,
                                 as_csv=True,
                                 destination=self.indicator_config['indicator']['data'][interval])

        # Get the timezone object for the desired time zone
        tz = pytz.timezone("Asia/Kolkata")

        # Get the current time in the specified time zone
        now = datetime.now(tz)

        # Print the current time in the specified time zone
        now = now.strftime("%Y-%m-%d %H:%M:%S %Z")
        print(f"[{now}] Downloaded {interval} data")

    def __monthly_fundamental_download(self):
        selected_stocks = self.selected_stocks_config
        tickers = [tick + '.NS' for tick in selected_stocks['stock']]
        download_stock_stats(tickers=tickers, destination=self.indicator_config['indicator']['fundamental'])
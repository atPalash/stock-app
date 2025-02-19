from apscheduler.schedulers.background import BackgroundScheduler
import pytz

from stock_app_py.scheduler.base.scheduler import Scheduler
from stock_app_py.system.src.command_handler import CommandHandler
from stock_app_py.utility.src.path_helper import get_app_path


class YahooScheduler(Scheduler):
    def __init__(
        self,
        indicator_config_file: str,
        selected_stocks_config_file: str,
        master_url: str,
    ) -> None:
        super().__init__(
            indicator_config_file=indicator_config_file,
            selected_stocks_config_file=selected_stocks_config_file,
            master_url=master_url,
        )
        self.schedulers = {}

        self.system_command_handler = CommandHandler(
            indicator_config_yaml=indicator_config_file,
            selected_stocks_yaml=selected_stocks_config_file,
        )

    def run(self):
        scheduler = BackgroundScheduler()
        for interval in self.indicator_config["indicator"]["data"]:
            self.__periodic_download(interval=interval)
            # if interval == "month":
            #     scheduler.add_job(
            #         self.__periodic_download,
            #         "cron",
            #         hour="16",
            #         day_of_week="mon-fri",
            #         timezone=pytz.timezone("Asia/Kolkata"),
            #         args=[interval],
            #     )
            # if interval == "week":
            #     scheduler.add_job(
            #         self.__periodic_download,
            #         "cron",
            #         hour="16",
            #         day_of_week="mon-fri",
            #         timezone=pytz.timezone("Asia/Kolkata"),
            #         args=[interval],
            #     )
            # if interval == "day":
            #     scheduler.add_job(
            #         self.__periodic_download,
            #         "cron",
            #         hour="16",
            #         day_of_week="mon-fri",
            #         timezone=pytz.timezone("Asia/Kolkata"),
            #         args=[interval],
            #     )
            # if interval == "hour":
            #     scheduler.add_job(
            #         self.__periodic_download,
            #         "cron",
            #         hour="9-16",
            #         minute="16",
            #         day_of_week="mon-fri",
            #         timezone=pytz.timezone("Asia/Kolkata"),
            #         args=[interval],
            #     )
            # elif interval == 'minute':
            #     scheduler.add_job(self.__periodic_download, 'cron', hour='9-16', minute='*',
            #                       day_of_week='mon-fri', timezone=pytz.timezone('Asia/Kolkata'), args=[interval])
            if interval == "minute5":
                scheduler.add_job(
                    self.__periodic_download,
                    "cron",
                    hour="9-16",
                    minute="*/5",
                    day_of_week="mon-fri",
                    timezone=pytz.timezone("Asia/Kolkata"),
                    args=[interval],
                )
            # if interval == "minute15":
            #     scheduler.add_job(
            #         self.__periodic_download,
            #         "cron",
            #         hour="9-16",
            #         minute="*/15",
            #         day_of_week="mon-fri",
            #         timezone=pytz.timezone("Asia/Kolkata"),
            #         args=[interval],
            #     )
            # if interval == "minute30":
            #     scheduler.add_job(
            #         self.__periodic_download,
            #         "cron",
            #         hour="9-16",
            #         minute="*/30",
            #         day_of_week="mon-fri",
            #         timezone=pytz.timezone("Asia/Kolkata"),
            #         args=[interval],
            #     )

            self.schedulers[interval] = scheduler

        scheduler.add_job(
            self.__weekly_fundamental_download,
            "cron",
            day_of_week="fri",
            hour="23",
            timezone=pytz.timezone("Asia/Kolkata"),
        )
        scheduler.start()

    def forceDownload(self, inter="", ticker="all"):
        if inter == "":
            for interval in self.indicator_config["indicator"]["data"]:
                self.__periodic_download(interval=interval, ticker=ticker)
        else:
            self.__periodic_download(interval=inter, ticker=ticker)
        # self.__weekly_fundamental_download()

    def __periodic_download(self, interval: str, ticker="all"):
        """Analysis method will include all the possible combination of the indicators.
        Donot call this method directly to avoid confusion, use the above methods.

        Args:
            interval (str): _description_
            add_latest (bool, optional): _description_. Defaults to False.
        """
        try:
            print(f"DEBUG yahoo scheduler {interval}")
            query = f"yahoofinance --ticker {ticker} --interval {interval} --do get --pandas 0  --csv 1"
            # just download the data, only print the errors
            ret = self.system_command_handler.execute(message=query, is_rest=False)
            if ret.errors != "":
                print("ERROR yahoo system", ret.errors)
            # self.__resample_ohlcv(ticker_dfs=ret.obj)
        except Exception as e:
            print("ERROR __periodic_download", e.args)

    def __weekly_fundamental_download(self):
        try:
            query = f"yahoofinance --ticker all --do fundamentals --pandas 0  --csv 1"
            # just download the data, only print the errors
            ret = self.system_command_handler.execute(message=query, is_rest=False)
            if ret.errors != "":
                print("ERROR yahoo fundamental download system", ret.errors)  # TODO
        except Exception as e:
            print("ERROR __weekly_fundamental_download", e.args)

    def __resample_ohlcv(self, ticker_dfs: dict):
        """Resample the data to the desired interval."""
        file_paths = read_config(get_app_path("indicator.yaml"))["indicator"]["data"]
        intervals_to_sample = {
            15: file_paths["minute15"],
            30: file_paths["minute30"],
            60: file_paths["hour"],
        }
        for ticker, df in ticker_dfs.items():
            try:
                for interval in intervals_to_sample.keys():
                    df = df.asfreq(
                        "5T"
                    )  # Ensure that the data is 5 minute timestamp are present
                    df.ffill(inplace=True)  # Forward fill missing data
                    resampled_df = df.resample(f"{interval}T", offset="15min").agg(
                        {
                            "Open": "first",
                            "High": "max",
                            "Low": "min",
                            "Close": "last",
                            "Volume": "sum",
                        }
                    )
                    resampled_df = resampled_df.between_time("09:15", "15:30")
                    resampled_df.to_csv(
                        f"{intervals_to_sample[interval]}/{ticker}.csv",
                    )
            except Exception as e:
                raise


if __name__ == "__main__":
    from stock_app_py.utility.src.yaml_parser import read_config

    config = read_config(get_app_path("config.yaml"))
    indicator_config_yaml = get_app_path("indicator.yaml")
    selected_stocks_yaml = get_app_path("selected_stocks.yaml")
    scheduler = YahooScheduler(indicator_config_yaml, selected_stocks_yaml, "dummy")
    scheduler.forceDownload(inter="minute5")

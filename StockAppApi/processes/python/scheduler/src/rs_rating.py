from apscheduler.schedulers.background import BackgroundScheduler
import pytz

from StockAppApi.processes.python.scheduler.base.scheduler import Scheduler
from StockAppApi.processes.python.system.src.command_handler import CommandHandler


class RsRating(Scheduler):
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
        scheduler.add_job(
            self.__periodic_download,
            "cron",
            hour="16",
            day_of_week="mon-fri",
            timezone=pytz.timezone("Asia/Kolkata"),
            args=[],
        )
        scheduler.start()

    def forceDownload(self):
        self.__periodic_download()

    def __periodic_download(self):
        """Create Rs rating csv file"""
        try:
            query = f"rsrating --do update"
            ret = self.system_command_handler.execute(
                message=query, is_rest=False
            )  # just download the data, only print the errors
            if ret.errors != "":
                print("ERROR nsestocklist system", ret.errors)
        except Exception as e:
            print("ERROR __periodic_download", e.args)


if __name__ == "__main__":
    from StockAppApi.base.python.src.yaml_parser import read_config

    configFolder = "StockAppApi/configuration/"
    config = read_config(configFolder + "config.yaml")
    indicator_config_yaml = configFolder + "indicator.yaml"
    selected_stocks_yaml = configFolder + "selected_stocks.yaml"
    scheduler = RsRating(indicator_config_yaml, selected_stocks_yaml, "dummy")
    scheduler.forceDownload()

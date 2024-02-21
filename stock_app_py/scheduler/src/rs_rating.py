from apscheduler.schedulers.background import BackgroundScheduler
import pytz

from stock_app_py.scheduler.base.scheduler import Scheduler
from stock_app_py.system.src.command_handler import CommandHandler
from stock_app_py.utility.src.path_helper import get_app_path


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
            print(f'DEBUG rs-rating scheduler')
            query = f"rsrating --do update"
            ret = self.system_command_handler.execute(
                message=query, is_rest=False
            )  # just download the data, only print the errors
            if ret.errors != "":
                print("ERROR nsestocklist system", ret.errors)
        except Exception as e:
            print("ERROR __periodic_download", e.args)


if __name__ == "__main__":
    from stock_app_py.utility.src.yaml_parser import read_config

    config = read_config(get_app_path('config.yaml'))
    indicator_config_yaml = get_app_path('indicator.yaml')
    selected_stocks_yaml = get_app_path('selected_stocks.yaml')
    scheduler = RsRating(indicator_config_yaml, selected_stocks_yaml, "dummy")
    scheduler.forceDownload()

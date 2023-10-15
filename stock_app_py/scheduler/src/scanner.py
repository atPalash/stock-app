from apscheduler.schedulers.background import BackgroundScheduler
import numpy
import pytz
import pandas
import multiprocessing
import matplotlib

matplotlib.use("Agg")

from stock_app_py.scheduler.base.scheduler import Scheduler
from stock_app_py.system.src.command_handler import CommandHandler
import mplfinance as mpf
from PIL import Image, ImageDraw, ImageFont


class Scanner(Scheduler):
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
        self.sample = {
            "hour": 80,
            "day": 60,
            "week": 40,
        }

    def run(self):
        self.__hourly_scan()
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            self.__hourly_scan,
            "cron",
            hour="9-16",
            minute="30",
            day_of_week="mon-fri",
            timezone=pytz.timezone("Asia/Kolkata"),
        )
        scheduler.start()
        self.schedulers["hour"] = scheduler

    def __hourly_scan(self):
        elder = self.__elder_scan()
        canslim = self.__canslim_scan()
        macdhist_week_divergence = self.__macd_histogram_divergence_scan("week")
        macdhist_day_divergence = self.__macd_histogram_divergence_scan("day")
        macdhist_hour_divergence = self.__macd_histogram_divergence_scan("hour")

        # plot analysed data
        for ticker in (
            self.selected_stocks_config["stock"] + self.selected_stocks_config["index"]
        ):
            try:
                self.__plot(
                    ticker=ticker,
                    elder=elder[elder["stock"] == ticker],
                    canslim=canslim.get(ticker, None),
                    macd_hist=macdhist_week_divergence[ticker],
                    interval="week",
                )
                self.__plot(
                    ticker=ticker,
                    elder=elder[elder["stock"] == ticker],
                    canslim=canslim.get(ticker, None),
                    macd_hist=macdhist_day_divergence[ticker],
                    interval="day",
                )
                self.__plot(
                    ticker=ticker,
                    elder=elder[elder["stock"] == ticker],
                    canslim=canslim.get(ticker, None),
                    macd_hist=macdhist_hour_divergence[ticker],
                    interval="hour",
                )
            except Exception as e:
                print(ticker, e.args)
                continue

    def __elder_scan(self):
        try:
            elder_query = f"elderimpulse --stock all --window 13 --n 100 --macd_fast_period 13 --macd_slow_period 26 --macd_signal_period 9 --latest 1"
            ret = self.system_command_handler.execute(elder_query)
            if ret.errors != "":
                print("ERROR elder system", ret.errors)
            return ret.obj
        except Exception as e:
            print("ERROR __elder_scan", e.args)

    def __macd_histogram_divergence_scan(self, interval):
        try:
            query = f"macdhistdivergencescan --ticker all --interval {interval} --do get --window 20 --n {self.sample[interval]} --latest 0"
            ret = self.system_command_handler.execute(query)
            if ret.errors != "":
                print(f"ERROR macdhist system for {interval}", ret.errors)
            return ret.obj
        except Exception as e:
            print("ERROR __macd_histogram_divergence_scan", e.args)

    def __canslim_scan(self):
        try:
            query = f"canslim --ticker all --do get --n 400"
            ret = self.system_command_handler.execute(query)
            if ret.errors != "":
                print("ERROR canslim system", ret.errors)
            return ret.obj
        except Exception as e:
            print("ERROR __canslim_scan", e.args)

    def __plot(self, **kwargs):
        try:
            interval = kwargs["interval"]
            ticker = kwargs["ticker"]
            samples = kwargs["macd_hist"].shape[0]

            # add signals from divergence scan
            additionals_list = []
            additionals_list = self.__get_macdhist_plot(
                macdhist_df=kwargs["macd_hist"], add_list_ref=additionals_list
            )

            ohlc = pandas.read_csv(
                f"{self.indicator_config['indicator']['data'][interval]}/{ticker}.csv",
                index_col=0,
                parse_dates=True,
            ).tail(samples)
            image_path = (
                f"{self.indicator_config['indicator']['plot'][interval]}/{ticker}.png"
            )
            mpf.plot(
                ohlc,
                addplot=additionals_list,
                volume=True,
                title=f"{ticker}_{interval}",
                type="candle",
                style="yahoo",
                savefig=image_path,
                figsize=(8, 6),
            )

            self.__add_info_text(
                image_path=image_path, canslim=kwargs["canslim"], elder=kwargs["elder"]
            )
        except Exception as e:
            print("ERROR __plot", e.args)

    def __get_macdhist_plot(self, macdhist_df, add_list_ref):
        samples = macdhist_df.shape[0]
        # find signals from divergence scan
        bulls = [numpy.nan for _ in range(samples)]
        bears = [numpy.nan for _ in range(samples)]
        for i in range(samples):
            if macdhist_df.iloc[i]["macdhist_divergence"] > 0:
                bulls[i] = macdhist_df.iloc[i]["Close"] * 0.99
            elif macdhist_df.iloc[i]["macdhist_divergence"] < 0:
                bears[i] = macdhist_df.iloc[i]["Close"] * 1.01

        if numpy.any(numpy.logical_not(numpy.isnan(bulls))):
            apd_bull = mpf.make_addplot(
                bulls, type="scatter", markersize=200, marker="^"
            )
            add_list_ref.append(apd_bull)
        if numpy.any(numpy.logical_not(numpy.isnan(bears))):
            apd_bear = mpf.make_addplot(
                bears, type="scatter", markersize=200, marker="v"
            )
            add_list_ref.append(apd_bear)
        macd_hist = mpf.make_addplot(
            macdhist_df["macdhist"],
            type="bar",
            width=0.7,
            panel=1,
            color="red",
            alpha=1,
            secondary_y=True,
        )
        add_list_ref.append(macd_hist)

        return add_list_ref

    def __add_info_text(self, image_path, **kwargs):
        # Open the PNG file
        img = Image.open(image_path)
        # Create an ImageDraw object
        draw = ImageDraw.Draw(img)

        # Define the font and size
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 10
        )

        # Define the text and position
        position = (10, 10)
        text = f""
        canslim = kwargs.get("canslim", None)
        if canslim is not None:
            quaterly_eps_growth = (
                f"quaterly eps growth\n{canslim.C.pct_change(periods=-1).to_string()}\n"
            )
            yearly_eps_growth = (
                f"yearly eps growth\n{canslim.A.pct_change(periods=-1).to_string()}\n"
            )
            relative_strength = f"relative strength\n{canslim.L.values.mean()}\n"
            market_direction = f"market direction\n{numpy.polyfit(canslim.M.index.values, canslim.M.values, 1)[0]}\n"
            shares_outstanding = f"shares outstanding\n{canslim.S.to_string()}\n"
            text = (
                text
                + f"--Canslim--\n"
                + quaterly_eps_growth
                + yearly_eps_growth
                + shares_outstanding
                + relative_strength
                + market_direction
            )

        elder = kwargs.get("elder", None)
        if elder is not None:
            text = text + f'--Elder impulse--\n {elder["trend"].to_string()}'

        # Draw the text on the image
        draw.text(position, text, font=font, fill="black")
        # Save the modified image
        img.save(image_path)

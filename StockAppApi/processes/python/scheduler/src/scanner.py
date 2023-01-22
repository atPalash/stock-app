from apscheduler.schedulers.background import BackgroundScheduler
import numpy
from datetime import datetime
import pandas
import multiprocessing

from StockAppApi.processes.python.scheduler.base.scheduler import Scheduler
from StockAppApi.processes.python.system.src.command_handler import CommandHandler
import mplfinance as mpf


class Scanner(Scheduler):
    def __init__(self, indicator_config_file: str, selected_stocks_config_file: str, master_url: str) -> None:
        super().__init__(indicator_config_file=indicator_config_file,
                         selected_stocks_config_file=selected_stocks_config_file,
                         master_url=master_url)
        self.schedulers = {}
        self.system_command_handler = CommandHandler(indicator_config_yaml=indicator_config_file,
                                                     selected_stocks_yaml=selected_stocks_config_file)

    def run(self):
        # for interval in self.indicator_config['indicator']['data']:
        # scheduler = BackgroundScheduler()
        # if interval == 'week':
        #     scheduler.add_job(self.__periodic_scan, 'cron', hour='17',
        #                       day_of_week='fri', timezone=pytz.timezone('Asia/Kolkata'), args=[interval])
        #     scheduler.start()
        # elif interval == 'day':
        #     scheduler.add_job(self.__periodic_download, 'cron', hour='16',
        #                       day_of_week='mon-fri', timezone=pytz.timezone('Asia/Kolkata'), args=[interval])
        #     scheduler.start()
        # if interval == 'hour':
        #     scheduler.add_job(self.__periodic_scan, 'cron', hour='9-16', minute='16',
        #                       day_of_week='mon-fri', timezone=pytz.timezone('Asia/Kolkata'))
        #     scheduler.start()
        # else:
        #     print(f"Error: This {interval} is not allowed")

        # self.schedulers[interval] = scheduler
        self.__periodic_scan()

    def __periodic_scan(self):
        """Perform period scan. Currently scan for macd divergence and elder impulse
        plot them directly to a ohlc plot for each stock
        """
        # elder_query = f"elderimpulse --stock all --window 13 --n 100 --macd_fast_period 13 --macd_slow_period 26 --macd_signal_period 9 --latest 1"
        # ret_elder = self.system_command_handler.execute(elder_query)

        sample = {
            'hour': 80,
            'day': 60,
            'week': 40,
        }
        for interval, val in self.indicator_config['indicator']['data'].items():
            query = f"macdhistdivergencescan --ticker all --interval {interval} --do get --window 20 --n {sample[interval]} --latest 1"
            ret = self.system_command_handler.execute(query).obj

            args = []
            for ticker, df in ret.items():
                args.append((df, sample[interval], interval, ticker))
            # Create a pool of worker processes
            with multiprocessing.Pool() as pool:
                pool.starmap(self._plot_result, args)

    def _plot_result(self, df:pandas.DataFrame, sample_size:int, interval:int, ticker:str):
        if (df['macdhist_divergence'] > 0).any() or (df['macdhist_divergence'] < 0).any():
            bulls = [numpy.nan for _ in range(sample_size)]
            bears = [numpy.nan for _ in range(sample_size)]
            for i in range(df.shape[0]):
                if df.iloc[i]['macdhist_divergence'] > 0:
                    bulls[i] = df.iloc[i]['Close']*0.99
                elif df.iloc[i]['macdhist_divergence'] < 0:
                    bears[i] = df.iloc[i]['Close']*1.01

                signals_list = []
                if numpy.any(numpy.logical_not(numpy.isnan(bulls))):
                    apd_bull = mpf.make_addplot(
                        bulls, type='scatter', markersize=200, marker='^')
                    signals_list.append(apd_bull)
                if numpy.any(numpy.logical_not(numpy.isnan(bears))):
                    apd_bear = mpf.make_addplot(
                        bears, type='scatter', markersize=200, marker='v')
                    signals_list.append(apd_bear)
                ohlc = pandas.read_csv(
                    f"{self.indicator_config['indicator']['data'][interval]}/{ticker}.csv", index_col=0, parse_dates=True).tail(sample_size)
                macd_hist = mpf.make_addplot(
                    df['macdhist'], type='bar', width=0.7, panel=1, color='red', alpha=1, secondary_y=True)
                signals_list.append(macd_hist)
                mpf.plot(ohlc, addplot=signals_list, volume=True, title=f"{ticker}_{interval}_divergence", type='candle',
                         style='yahoo', savefig=f"{self.indicator_config['indicator']['plot'][interval]}/{ticker}.png")

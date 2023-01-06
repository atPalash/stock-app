import pandas

from StockAppApi.base.python.src.yaml_parser import read_config
from StockAppApi.base.python.src.message_parser import parse_message

from StockAppApi.processes.python.talib.src.ema import Ema
from StockAppApi.processes.python.talib.src.macd import Macd


class Aggregator:
    def __init__(self, indicator_config_file: str) -> None:
        """Aggregator of all the supported indicators responsible for cleaning user
        queries and making queries to the indicator as required. Sets up the 
        data required by the indicators.

        Args:
            indicator_config_file (str): indicator config. Currently includes path
            for reading the ohlc csvs.
        """
        self.indicator_indicator_config_file = indicator_config_file
        self.indicators = {
            "ema": Ema
        }

    def get_analysis(self, query: str):
        """Get anlysed result based on the query. The query is in 2 parts
        <main_command> | <sub-command>. Currently lets assume only one sub-command
        is allowed. The user can send a series of query and filter the results based
        on that.

        Args:
            query (str): user defined query
        """
        indicator_config = read_config(
            self.indicator_indicator_config_file)['indicator']

        arguments = parse_message(message=query)
        main_command = arguments[0]
        sub_command = arguments[2]
        stock = ""
        interval = ""

        if main_command['command'] == "select":
            stock = main_command['stock']
            interval = main_command['interval']

        if stock == "" or interval == "":
            raise Exception("Must define stock and interval")

        ohlc = indicator_config['data'][interval]
        stock_csv = f'{ohlc}/{stock}.csv'
        data = pandas.read_csv(stock_csv)
        result = ""
        ohlc_type = sub_command.get('ohlc', 'Close')
        if sub_command['indicator'] == "ema":
            window = int(sub_command.get('window', 20))
            ema_name = f'{stock}_{interval}_ema_{window}'
            parameter = {'ohlc': ohlc_type, 'window': window}
            indicator = Ema(name=ema_name, type=sub_command['indicator'],
                            ticker=stock, ohlc=data, parameter=parameter)
            result = indicator.execute_command(
                sub_command['command'], sub_command.get('condition', ""))
        elif 'macd' in sub_command['indicator']:
            fastperiod = int(sub_command.get('fastperiod', 12))
            slowperiod = int(sub_command.get('slowperiod', 26))
            signalperiod = int(sub_command.get('signalperiod', 9))
            macd_name = f'{sub_command["indicator"]}_{ohlc_type}_{fastperiod}_{slowperiod}_{signalperiod}_{stock}'
            parameter = {'ohlc': ohlc_type, 'fastperiod': fastperiod,
                        'slowperiod': slowperiod, 'signalperiod': signalperiod}
            indicator = Macd(name=macd_name, type=sub_command['indicator'], 
                             ticker=stock, ohlc=data, parameter=parameter)
            result = indicator.execute_command(sub_command['command'], 
                                               sub_command.get('condition', ""))
        print(result)
                        
    ''' No need to do periodic analysis
    def stop_sub_commandhedulers(self):
        for _, sub_commandheduler in self.sub_commandhedulers.items():
            sub_commandheduler.shutdown(wait=False)
        # self.test_sub_commandheduler.shutdown(wait=False)

    def __init_sub_commandheduler(self):
        for interval in read_config(self.indicator_indicator_config_file)['indicator']['data']:
            sub_commandheduler = Backgroundsub_commandheduler()
            if interval == 'week':    
                sub_commandheduler.add_job(self.__periodic_analysis, 'cron', hour='16', day_of_week='fri' , timezone=pytz.timezone('Asia/Kolkata'), args=[interval])
                # sub_commandheduler.start()
            elif interval == 'day':
                sub_commandheduler.add_job(self.__periodic_analysis, 'cron', hour='16', day_of_week='mon-fri' , timezone=pytz.timezone('Asia/Kolkata'), args=[interval])
                # sub_commandheduler.start()
            elif interval == 'hour':
                sub_commandheduler.add_job(self.__periodic_analysis, 'cron', hour='9-16', minute='16', day_of_week='mon-fri' , timezone=pytz.timezone('Asia/Kolkata'), args=[interval])
                sub_commandheduler.start()
            else:
                print(f"Error: This {interval} is not allowed")
            
            self.sub_commandhedulers[interval] = sub_commandheduler
        
        sub_commandheduler = Backgroundsub_commandheduler()
        sub_commandheduler.add_job(self.__latest_analysis, 'cron', hour='9-16', minute='*/30', day_of_week='mon-fri' , timezone=pytz.timezone('Asia/Kolkata'))
        sub_commandheduler.start()
        self.sub_commandhedulers['latest'] = sub_commandheduler 
    
    def __periodic_analysis(self, interval: str):
        self.__do_analysis(interval, False)
    
    def __latest_analysis(self):
        # get the latest ohlc and calculate the indicator based on other intervals
        self.__do_analysis('hour', True)
        # self.__do_analysis('day', True)
        # self.__do_analysis('week', True)
        
    def __do_analysis(self, interval: str, add_latest=False):
        """
        Analysis method will include all the possible combination of the indicators.
        Donot call this method directly to avoid confusion, use the above methods. 

        Args:
            interval (str): _desub_commandription_
            add_latest (bool, optional): _desub_commandription_. Defaults to False.
        """
        indicator_config = read_config(self.indicator_indicator_config_file)['indicator']

        ohlc = indicator_config['data'][interval]
        stock_csvs = glob.glob(f'{ohlc}/*.csv')
        
        latest_df = pandas.DataFrame
        if add_latest:
            latest_df = download_latest_data(tickers=[os.path.split(file)[1].split('.')[0] + ".NS" for file in stock_csvs])
                
        for file in stock_csvs:
            stock_df = pandas.read_csv(file)
            _, stock = os.path.split(file)
            stock = stock.split('.')[0]
            last_row_index = stock_df.index.max()
            if len(latest_df) > 0:
                for col_name, col_value in latest_df[stock + '.NS'].items():
                    stock_df.loc[last_row_index + 1, col_name] = col_value.values[0]
            
            if indicator_config['ema'] :
                for window in indicator_config['ema'][interval]['parameter']['window']:
                    ema = Ema(f'EMA_{interval}_{window}_{stock}', ohlc=stock_df,
                                parameter={'ohlc': indicator_config['ema'][interval]['parameter']['ohlc'],
                                            'window': window})
                    result = ema.do_analysis()
                    stock_df[f'EMA_{window}'] = result
            
            self.latest_analysed_df[stock] = { interval : stock_df }
            if not add_latest:
                stock_df.to_csv(file, index=False)
    '''


if __name__ == "__main__":
    configFolder = "StockAppApi/configuration/"
    indicator_config_yaml = configFolder + "indicator.yaml"

    # indicator_config = read_config(indicator_config_yaml)
    aggregator = Aggregator(indicator_config_yaml)
    while True:
        inp = input("Enter")

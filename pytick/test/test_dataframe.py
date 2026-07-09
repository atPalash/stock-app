import os

from dotenv import load_dotenv

from pytick.dataframe import notification
from pytick.dataframe.dataframe import DataFrameHandler
from pytick.query.query import QueryHandler
from pytick.utility.utility import read_config



load_dotenv()

config = os.environ.get("CONFIG_FILE")
app_config = read_config(file_path=config)
indicators = app_config.get('indicators', {})
tz = app_config.get('tz', 'Asia/Kolkata')
data_handler = DataFrameHandler(tz=tz, indicators=indicators, interval_limits=app_config.get('interval_limits', {}))
notification_handler = notification.NotificationHandler(
    tz=tz, max_rows=1000, app_data_path=app_config.get('app_data_path', ''))
query_handler = QueryHandler(data_handler=data_handler,
                            notification_handler=notification_handler,
                            interval_translation={v: k for k, v in app_config.get('interval_translation', {}).items()},
                            interval_seconds=app_config.get('interval_seconds', {}))

def test_set_tables_indices():   
    indices = ['INDIAVIX', 'NSEI']
    data_handler.set_tables(tickers=indices, interval='1d', suffix='', prefix='^')  # Set the OHLC tables for the specified tickers and interval
    assert data_handler.tables['1d'] is not None, "Tables for interval '1d' should not be None"
    assert not data_handler.tables['1d']['INDIAVIX'].empty, "Tables for interval '1d' should not be empty"

def test_set_add_tables():
    tickers = ['RELIANCE', 'TCS']
    data_handler.set_tables(tickers=tickers, interval='1d', suffix='.NS', prefix='')
    assert data_handler.tables['1d'] is not None, "Tables for interval '1d' should not be None"
    assert not data_handler.tables['1d']['RELIANCE'].empty, "Tables for interval '1d' should not be empty"
    
    indices = ['INDIAVIX', 'NSEI']
    data_handler.add_tables(tickers=indices, interval='1d', suffix='', prefix='^')  # Set the OHLC tables for the specified tickers and interval
    assert data_handler.tables['1d'] is not None, "Tables for interval '1d' should not be None"
    assert not data_handler.tables['1d']['INDIAVIX'].empty, "Tables for interval '1d' should not be empty"
    assert len(data_handler.tables['1d'].keys()) == 4, "There should be 4 tickers in the tables for interval '1d' after adding indices"

def test_query_with_indices():
    indices = ['INDIAVIX', 'NSEI']
    data_handler.set_tables(tickers=indices, interval='1d', suffix='', prefix='^')  # Set the OHLC tables for the specified tickers and interval
    gherkin = """
Feature: pytick llm
Scenario: EMA10 and EMA20 rate analysis over 10 samples with close proximity and 0.5*ATR10
Given stocks from list INDIAVIX, NSEI
When let ema10 = latest in 1 samples of day close ema 10
* let ema20 = latest in 1 samples of day close ema 20
* let ema10_rate = rate in 10 samples of day close ema 10
* let ema20_rate = rate in 10 samples of day close ema 20
* let close = latest in 1 samples of day close
* let atr10 = latest in 1 samples of day close atr 10
Then list buy = tickers with (ema10_rate > 0) & (ema20_rate > 0) & (abs(close - ema10) < 0.25 * atr10)
"""
    result = query_handler.get_gherkin_result(gherkin_str=gherkin)[1]
    bull = result[0]
    assert isinstance(bull, dict), "Bull result should be a dict"

if __name__ == "__main__":
    test_query_with_indices()
    print("All tests passed.")
from unittest import mock
import inspect
import os
import pandas as pd
import pytz
import inspect
import asyncio
import pytest

from pytick.dataframe.dataframe import DataFrameHandler
from pytick.bot.discordbot import BotConfig, DiscordBot
from pytick.query import query
from pytick.utility.utility import read_config

config = os.environ.get("CONFIG_FILE")
app_config = read_config(file_path=config)
users_config_path = os.environ.get("USERS_DIR")

class DummyNotificationHandler:
    def get_corporate_actions(self, *args, **kwargs):
        return {}
    def get_corporate_actions_dfs(self, *args, **kwargs):
        return {}
    
class TestQueryHandler:    
    tickers = ["TCS", "BEL", "SBIN"]
    indicators = app_config.get('indicators', {})
    cron_schedules = app_config.get('cron_schedules', {})
    cron_notification = app_config.get('cron_notification', {})
    tz = app_config.get('tz', 'Asia/Kolkata')
    data_handler = DataFrameHandler(tz=tz, indicators=indicators, test_data_path="/home/palash/app/pytick/test/data")
    data_handler.set_tables(tickers, "1d")
    data_handler.set_tables(tickers, "5m")
    notification_handler = DummyNotificationHandler()
    def __init__(self):
        self.gherkin_handler = query.QueryHandler(data_handler=self.data_handler, 
                                        notification_handler=self.notification_handler,
                                        interval_translation={v: k for k, v in app_config.get('interval_translation', {}).items()},
                                        interval_seconds=app_config.get('interval_seconds', {}))
    def getQueryHandler(self):
        return self.gherkin_handler

def make_bot_config(tmp_path):
    zerodha_df = pd.DataFrame(columns=["tradingsymbol", "exchange", "instrument_token"])
    return BotConfig(
        token="fake-token",
        command_prefix='/',
        query_handler=TestQueryHandler().getQueryHandler(),
        notification_handler=DummyNotificationHandler(),
        llm_convert_msg='',
        tz=pytz.timezone('Asia/Kolkata'),
        schedules={'1d': {}},
        users_config_path=str(f"{tmp_path}/users"),
        update_users_callback=lambda *args, **kwargs: None,
        zerodha_df=zerodha_df,
        trading_view_url=app_config.get('trading_view_url', ''),
        zerodha_url=app_config.get('zerodha_url', ''),
        link_type='zerodha',
        backtest_iterations=1,
        default_ticker='SBIN'
    )

bot_config = make_bot_config(tmp_path="/home/palash/app/pytick/test")
bot = DiscordBot(bot_config)

class DiscordBotWrapper:
    class DummyAuthor:
        def __init__(self):
            self.id = 12345
            self.name = 'tester'
            self.global_name = 'tester'
            self.mention = '@tester'

    class DummyCtx:
        def __init__(self, bot, command_name='run'):
            self.author = DiscordBotWrapper.DummyAuthor()
            self.command = bot.bot.get_command(command_name)
            # collect sends
            self.sent = []

        async def send(self, *args, **kwargs):
            self.sent.append((args, kwargs))

    def __init__(self):
        self.bot = bot
        self.run_ctx = DiscordBotWrapper.DummyCtx(self.bot, 'run')
        self.edit_ctx = DiscordBotWrapper.DummyCtx(self.bot, 'edit')

async def run_command(query:str):
    import pytick.bot.commands as cmd_mod
    try:
        discord_bot_wrapper = DiscordBotWrapper()
        await cmd_mod.run(discord_bot_wrapper.run_ctx, (query,))
        # fields = discord_bot_wrapper.run_ctx.sent[2][1]['embed'].fields
        return discord_bot_wrapper.run_ctx.sent
    except Exception as e:
        raise e
    
@pytest.mark.asyncio
async def test_valid_run():
    query_expectation = [
        {
            "query": """
Feature: pytick llm
Scenario: Movers greater than 1% with respect to previous day close analysis
Given stocks from index nifty50
When let prev_close = oldest in 2 samples of day close
* let close = latest in 1 samples of minute5 close
Then list bull = tickers with ((close - prev_close) / prev_close > 0.01)
* list bear = tickers with ((prev_close - close) / prev_close > 0.01)
            """,
            "expected_fields": ['bull', 'bear'],
            "expected_values": ['SBIN', 'BEL']
        },
        {
            "query": """
Feature: pytick llm  
Scenario: EMA10 and EMA20 rising and falling analysis over 10 samples with close proximity and ATR10  
Given stocks from index nifty50  
When let ema10 = rate in 10 samples of day close ema 10  
* let ema20 = rate in 10 samples of day close ema 20  
* let close = latest in 1 samples of day close  
* let atr10 = latest in 1 samples of day close atr 10  
Then list bull = tickers with (ema10 > 0) & (ema20 > 0) & (abs(close - ema10) / ema10 < 4 * atr10)  
* list bear = tickers with (ema10 < 0) & (ema20 < 0) & (abs(close - ema10) / ema10 < 4 * atr10)
            """,
            "expected_fields": ['bull', 'bear'],
            "expected_values": ['TCS']
        },
        {
            "query": """
Feature: pytick llm  
Scenario: Edit bull as higher close and bear as lower close with high and low conditions for 3 days  
Given stocks from index nifty50  
When let close1 = latest in 1 samples of day close  
* let close2 = oldest in 2 samples of day close  
* let close3 = oldest in 3 samples of day close  
* let high1 = latest in 1 samples of day high  
* let high2 = oldest in 2 samples of day high  
* let high3 = oldest in 3 samples of day high  
* let low1 = latest in 1 samples of day low  
* let low2 = oldest in 2 samples of day low  
* let low3 = oldest in 3 samples of day low  
Then list bull = tickers with ((close1 > close2) & (close2 > close3)) | ((high1 > high2) & (high2 > high3))
* list bear = tickers with ((close1 < close2) & (close2 < close3)) | ((low1 < low2) & (low2 < low3))
            """,
            "expected_fields": ['bull', 'bear'],
            "expected_values": ['SBIN', 'TCS']
        },
    ]

    for item in query_expectation:
        query = item['query']
        expected_fields = item['expected_fields']
        expected_values = item['expected_values']
        sent = await run_command(query)
        fields = sent[2][1]['embed'].fields
        for field_name in expected_fields:
            assert any(field.name == field_name for field in fields), f"Expected field '{field_name}' in embed"
        for value in expected_values:
            assert any(value in field.value for field in fields), f"Expected value '{value}' in embed values"

@pytest.mark.asyncio
async def test_error_run():
    query_expectation = [
        {
            "query": """
Feature: pytick llm  
Scenario: Test error with invalid indicator ema11 is not supported
Given stocks from index nifty50  
When let ema11 = rate in 10 samples of day close ema 11  
* let ema22 = rate in 10 samples of day close ema 22  
* let close = latest in 1 samples of day close  
* let atr10 = latest in 1 samples of day close atr 10  
Then list bull = tickers with (ema11 > 0) & (ema22 > 0) & (abs(close - ema11) / ema11 < 4 * atr10)  
* list bear = tickers with (ema11 < 0) & (ema22 < 0) & (abs(close - ema11) / ema11 < 4 * atr10)
            """,
            "expected_errors": ['Exception', 'calculating variable ema11'],
        },
        {
            "query": """
Feature: pytick llm  
Scenario: Test error with unknown indicator key ema11
Given stocks from index nifty50  
When let ema10 = rate in 10 samples of day close ema 10  
* let ema20 = rate in 10 samples of day close ema 20  
* let close = latest in 1 samples of day close  
* let atr10 = latest in 1 samples of day close atr 10  
Then list bull = tickers with (ema11 > 0) & (ema22 > 0) & (abs(close - ema11) / ema11 < 4 * atr10)  
* list bear = tickers with (ema11 < 0) & (ema22 < 0) & (abs(close - ema11) / ema11 < 4 * atr10)
            """,
            "expected_errors": ['Exception', 'Exception evaluating condition', 'ema11'],
        },
        {
            "query": """
Feature: pytick llm  
Scenario: Test error with invalid gherkin When before Given
When let ema10 = rate in 10 samples of day close ema 10  
* let ema20 = rate in 10 samples of day close ema 20  
* let close = latest in 1 samples of day close  
* let atr10 = latest in 1 samples of day close atr 10  
Given stocks from index nifty50  
Then list bull = tickers with (ema11 > 0) & (ema22 > 0) & (abs(close - ema11) / ema11 < 4 * atr10)  
* list bear = tickers with (ema11 < 0) & (ema22 < 0) & (abs(close - ema11) / ema11 < 4 * atr10)
            """,
            "expected_errors": ['Exception', 'When found before'],
        },
        {
            # No Scenario keyword
            "query": """
Feature: pytick llm  
Given stocks from index nifty50  
When let ema10 = rate in 10 samples of day close ema 10  
* let ema20 = rate in 10 samples of day close ema 20  
* let close = latest in 1 samples of day close  
* let atr10 = latest in 1 samples of day close atr 10  
Then list bull = tickers with (ema11 > 0) & (ema22 > 0) & (abs(close - ema11) / ema11 < 4 * atr10)  
* list bear = tickers with (ema11 < 0) & (ema22 < 0) & (abs(close - ema11) / ema11 < 4 * atr10)
            """,
            "expected_errors": ['Exception', 'Given found before Scenario'],
        },
        {
            "query": """
Feature: pytick llm  
Scenario: Test error with invalid syntax in condition
Given stocks from index nifty50  
When let ema10 = rate in 10 samples of day close ema 10  
* let ema20 = rate in 10 samples of day close ema 20  
* let close = latest in 1 samples of day close  
* let atr10 = latest in 1 samples of day close atr 10  
Then list bull = tickers with (ema10 === 0) & (ema20 > 0) & (abs(close - ema10) / ema10 < 4 * atr10)  
* list bear = tickers with (ema10 < 0) & (ema20 < 0) & (abs(close - ema10) / ema10 < 4 * atr10)
            """,
            "expected_errors": ['Exception', 'Exception evaluating condition', 'invalid syntax', 'ema10 === 0'],
        },
        {
            "query": """
Feature: pytick llm  
Scenario: Test index not found error 
Given stocks from index nifty500  
When let ema100 = rate in 100 samples of day close ema 100  
* let ema200 = rate in 200 samples of day close ema 200  
* let close = latest in 1 samples of day close  
* let atr10 = latest in 1 samples of day close atr 10  
Then list bull = tickers with (ema100 > 0) & (ema200 > 0) & (abs(close - ema100) / ema100 < 4 * atr10)  
* list bear = tickers with (ema100 < 0) & (ema200 < 0) & (abs(close - ema100) / ema100 < 4 * atr10)
            """,
            "expected_errors": ['Exception', 'Given stocks from index nifty500', 'Allowed values', 'nifty50'],
        },
    ]

    async def test_func(item):
        query = item['query']
        sent = await run_command(query)
        error = sent[2][0][0]
        for expected_error in item['expected_errors']:
            assert expected_error in error, f"Expected error '{expected_error}' in '{error}'"

    for item in query_expectation:
        await test_func(item)
        
#     await test_func(        {
#             "query": """
# Feature: pytick llm  
# Scenario: Close price greater than 200 EMA analysis  
# Given stocks from index nifty50  
# When let close = latest in 1 samples of day close  
# * let ema200 = latest in 1 samples of day close ema 200  
# Then list result = tickers with (close > ema200)
#             """,
#             "expected_errors": ['Exception', 'Given stocks from index nifty500', 'Allowed values', 'nifty50'],
#         })  

@pytest.mark.asyncio
async def test_data_missing():
    query_expectation = [
        {
            "query": """
Feature: pytick llm  
Scenario: TMPV doesn't support 200 EMA since it insufficient data, the query should pass with other tickers
Given stocks from index nifty50  
When let close = latest in 1 samples of day close  
* let ema200 = latest in 1 samples of day close ema 200  
Then list result = tickers with (close > ema200)
            """,
            "expected_fields": ['result'],
            "expected_values": ['SBIN', 'BEL']
        },
    ]

    async def test_func(item):
        query = item['query']
        expected_fields = item['expected_fields']
        expected_values = item['expected_values']
        sent = await run_command(query)
        fields = sent[2][1]['embed'].fields
        for field_name in expected_fields:
            assert any(field.name == field_name for field in fields), f"Expected field '{field_name}' in embed"
        for value in expected_values:
            assert any(value in field.value for field in fields), f"Expected value '{value}' in embed values"
    for item in query_expectation:
        await test_func(item)
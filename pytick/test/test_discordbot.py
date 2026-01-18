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
                                        interval_translation={v: k for k, v in app_config.get('interval_translation', {}).items()})
    def getQueryHandler(self):
        return self.gherkin_handler
    
def make_bot_config(tmp_path):
    users_dir = tmp_path / "users"
    users_dir.mkdir()
    zerodha_df = pd.DataFrame(columns=["tradingsymbol", "exchange", "instrument_token"])
    return BotConfig(
        token="fake-token",
        command_prefix='/',
        query_handler=TestQueryHandler().getQueryHandler(),
        notification_handler=DummyNotificationHandler(),
        llm_convert_msg='',
        tz=pytz.timezone('Asia/Kolkata'),
        schedules={'1d': {}},
        users_config_path=str(users_dir),
        update_users_callback=lambda *args, **kwargs: None,
        zerodha_df=zerodha_df,
        trading_view_url=app_config.get('trading_view_url', ''),
        zerodha_url=app_config.get('zerodha_url', ''),
        link_type='zerodha',
        backtest_iterations=1,
        default_ticker='SBIN'
    )


def test_commands_registered(tmp_path):
    """DiscordBot should register coroutine functions from pytick.bot.commands as commands."""
    config = make_bot_config(tmp_path)
    bot_wrapper = DiscordBot(config)

    # Import the commands module and get coroutine function names
    import pytick.bot.commands as cmd_mod
    supported = [name for name, func in inspect.getmembers(cmd_mod, inspect.iscoroutinefunction) if not name.startswith('_')]

    assert len(supported) > 0, "No coroutine commands found in pytick.bot.commands"

    for name in supported:
        cmd = bot_wrapper.bot.get_command(name)
        assert cmd is not None, f"Command {name} should be registered"
        # extras should include reference to the DiscordBot instance
        assert cmd.extras.get('discordbot') is bot_wrapper


@pytest.mark.asyncio
async def test_run_command(tmp_path):
    """Simulate invoking the /run command and ensure it attempts to send query and embed results."""
    config = make_bot_config(tmp_path)
    bot_wrapper = DiscordBot(config)

    # create a fake ctx with minimal attributes used by run()
    class DummyAuthor:
        def __init__(self):
            self.id = 12345
            self.name = 'tester'
            self.global_name = 'tester'
            self.mention = '@tester'

    class DummyMessage:
        def __init__(self, content=''):
            self.content = content
            self.reference = mock.Mock(resolved=mock.Mock(content=''))

    class DummyCtx:
        def __init__(self):
            self.author = DummyAuthor()
            # self.bot = bot_wrapper.bot
            # self.message = DummyMessage(content='/run')
            # self.invoked_with = 'run'
            self.command = bot_wrapper.bot.get_command('run')
            # collect sends
            self.sent = []

        async def send(self, *args, **kwargs):
            self.sent.append((args, kwargs))

    ctx = DummyCtx()

    # # Ensure query pre-check returns empty so run() will call edit() path
    # # patch edit to return a simple gherkin query string
    import pytick.bot.commands as cmd_mod
    # async def fake_edit(c, *a, **k):
    #     return "Feature: test\nScenario: s"

    # monkeypatch = pytest.MonkeyPatch()
    try:
        # monkeypatch.setattr(cmd_mod, 'edit', fake_edit)

        query = """
Feature: pytick llm
Scenario: Movers greater than 1% with respect to previous day close analysis
Given stocks from index nifty50
When let prev_close = oldest in 2 samples of day close
* let close = latest in 1 samples of minute5 close
Then list bull = tickers with ((close - prev_close) / prev_close > 0.01)
* list bear = tickers with ((prev_close - close) / prev_close > 0.01)
            """
        # call the run command coroutine directly
        await cmd_mod.run(ctx, (query,))

        # Check that the ctx.send was called at least once
        assert len(ctx.sent) >= 1
        embedded_fields = ctx.sent[2][1]['embed'].fields
        assert any(field.name == 'bull' for field in embedded_fields), "Expected 'bull' field in embed"
        assert any(field.name == 'bear' for field in embedded_fields), "Expected 'bear' field in embed"
        assert any('SBIN' in field.value for field in embedded_fields), "Expected 'SBIN' in embed values"
        assert any('BEL' in field.value for field in embedded_fields), "Expected 'BEL' in embed values"
    except Exception as e:
        raise e

if __name__ == "__main__":
    TestQueryHandler()
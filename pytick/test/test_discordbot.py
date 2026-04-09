import asyncio
import os

import discord
import pytest

from pytick.bot.discordbot import BotConfig, DiscordBot
from pytick.test.utility import TestQueryHandler, DummyNotificationHandler
import logging
from dotenv import load_dotenv
import pandas
from pytick.utility.utility import get_logger, read_config, read_file
from unittest.mock import AsyncMock, MagicMock

logger = get_logger(__file__, logging.DEBUG)
load_dotenv()
app_config = read_config(file_path=os.environ.get("CONFIG_FILE"))
gherkin_handler = TestQueryHandler().getQueryHandler()
bot_config = BotConfig(
    token=os.getenv('DISCORD_BOT_TOKEN', ''),
    command_prefix='/',
    query_handler=gherkin_handler,
    notification_handler=DummyNotificationHandler(),
    llm_convert_msg=app_config.get('discord_llm_msg', ''),
    tz=app_config.get('tz', 'Asia/Kolkata'),
    schedules=app_config.get('cron_schedules', {}),
    zerodha_df=pandas.read_csv(app_config.get(
        "zerodha_instrument_tokens_path", "")),
    trading_view_url=app_config.get('trading_view_url', ''),
    zerodha_url=app_config.get('zerodha_url', ''),
    link_type=app_config.get('link_type', 'zerodha'),
    backtest_iterations=app_config.get('backtest_iterations', 10),
    default_ticker=app_config.get('default_ticker', 'SBIN'),
    redis_url=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    convo_ttl_seconds=int(os.getenv('CONVO_TTL_SECONDS', '900')),
    guild_id=int(os.getenv('DISCORD_GUILD_ID', '0')),
    modal_timeout=120,
    llm_timeout=60,
    ollama_model='gemma3',
    openai_model='gpt-5.4',
    llm_prompt=read_file(file_path=os.path.join(app_config.get(
        'app_data_path', ''), "llm_prompt_init.prompt.md")),
    retry_prompt=read_file(file_path=os.path.join(app_config.get(
        'app_data_path', ''), "llm_prompt_retry.prompt.md")),
    joining_prompt=read_file(file_path=os.path.join(app_config.get(
        'app_data_path', ''), "getting_started.md")),
    disclaimer=read_file(file_path=os.path.join(app_config.get(
        'app_data_path', ''), "disclaimer.md"))
)
discord_bot = DiscordBot(config=bot_config)


@pytest.mark.asyncio
async def test_trade():
    gherkin = """
Feature: pytick llm  
Scenario: Test trade execution conditions
Given stocks from index nifty50  
When let atr = latest in 1 samples of minute5 close atr 10  
And let day_atr = latest in 1 samples of day close atr 10 
And let open_day = latest in 1 samples of day open
* let close = latest in 1 samples of minute5 close
* let vwap = latest in 1 samples of minute5 close vwap 10
Then list sell = tickers with abs(close - vwap) > 2 * atr & close > vwap & abs(close - open_day) > day_atr
* list buy = tickers with abs(close - vwap) > 2 * atr & close < vwap & abs(close - open_day) > day_atr
"""
    discord_bot.set_convo_store()
    result = await discord_bot.do_sub_run(interval="5m")
    sell = result[0]
    buy = result[1]
    expected_sell = {'sell': []}
    expected_buy = {'buy': []}
    assert isinstance(sell, dict), "Sell result should be a dict"
    assert isinstance(buy, dict), "Buy result should be a dict"
    assert sell == expected_sell, f"Expected sell result {expected_sell} but got {sell}"
    assert buy == expected_buy, f"Expected buy result {expected_buy} but got {buy}"


if __name__ == "__main__":
    result = asyncio.run(test_trade())
    print("Test result:", result)

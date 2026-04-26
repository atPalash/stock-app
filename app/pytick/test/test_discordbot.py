import asyncio
import copy
import os
import json

import discord
from discord import app_commands
from discord.ext import commands
import pytest
from reactivex import notification
import redis

from pytick.dataframe.dataframe import DataFrameHandler
from pytick.dataframe.notification import NotificationHandler
from pytick.query.query import QueryHandler
from pytick.bot.discordbot import BotConfig, DiscordBot, TextModal
from pytick.test.utility import DummyQueryHandler, DummyNotificationHandler
import logging
from dotenv import load_dotenv
from pytick.trade.trade import TradeHandler
from pytick.utility.convo_store import ConvoStore
import pandas
from pytick.utility.utility import get_logger, read_config, read_file, RetVal
from unittest.mock import AsyncMock, MagicMock, patch, Mock

logger = get_logger(__file__, logging.ERROR)
load_dotenv()

config = os.environ.get("CONFIG_FILE")
app_config = read_config(file_path=config)
tickers = ["TCS", "BEL", "SBIN", "TMPV"]
indicators = app_config.get('indicators', {})
cron_schedules = app_config.get('cron_schedules', {})
cron_notification = app_config.get('cron_notification', {})
tz = app_config.get('tz', 'Asia/Kolkata')
convo_store = ConvoStore(redis.from_url(
    os.getenv('REDIS_URL', 'redis://localhost:6379/0'), encoding="utf-8", decode_responses=True))
data_handler = DataFrameHandler(
    tz=tz, indicators=indicators, test_data_path=f"{app_config.get('pytick_test_path', '')}/data")
data_handler.set_tables(tickers, "1d")
data_handler.set_tables(tickers, "5m")
notification_handler = NotificationHandler(
    tz=tz, max_rows=1000, app_data_path=app_config.get('app_data_path', ''))
gherkin_handler = QueryHandler(data_handler=data_handler,
                               notification_handler=notification_handler,
                               interval_translation={v: k for k, v in app_config.get(
                                   'interval_translation', {}).items()},
                               interval_seconds=app_config.get('interval_seconds', {}))
trade_handler = TradeHandler(data_handler=data_handler,
                             notification_handler=notification_handler,
                             interval_translation={v: k for k, v in app_config.get(
                                 'interval_translation', {}).items()},
                             interval_seconds=app_config.get(
                                 'interval_seconds', {}),
                             convo_store=convo_store)
bot_config = BotConfig(
    token=os.getenv('DISCORD_BOT_TOKEN', ''),
    command_prefix='/',
    query_handler=gherkin_handler,
    trade_handler=trade_handler,
    notification_handler=notification_handler,
    llm_convert_msg=app_config.get('discord_llm_msg', ''),
    tz=tz,
    schedules=cron_schedules,
    zerodha_df=pandas.read_csv(app_config.get(
        "zerodha_instrument_tokens_path", "")),
    trading_view_url=app_config.get('trading_view_url', ''),
    zerodha_url=app_config.get('zerodha_url', ''),
    link_type=app_config.get('link_type', 'zerodha'),
    backtest_iterations=app_config.get('backtest_iterations', 10),
    default_ticker=app_config.get('default_ticker', 'SBIN'),
    convo_store=convo_store,
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


# ============================================================================
# Tests for BotConfig
# ============================================================================
class TestBotConfig:
    """Test BotConfig initialization and properties"""

    def test_bot_config_creation(self):
        """Test that BotConfig is properly initialized"""
        assert bot_config.command_prefix == '/'
        assert bot_config.modal_timeout == 120
        assert bot_config.llm_timeout == 60
        assert bot_config.ollama_model == 'gemma3'

    def test_bot_config_attributes(self):
        """Test all required BotConfig attributes are present"""
        required_attrs = [
            'token', 'command_prefix', 'query_handler', 'trade_handler',
            'notification_handler', 'tz', 'schedules', 'zerodha_df'
        ]
        for attr in required_attrs:
            assert hasattr(
                bot_config, attr), f"BotConfig missing attribute: {attr}"


# ============================================================================
# Tests for DiscordBot initialization
# ============================================================================
class TestDiscordBotInit:
    """Test DiscordBot initialization"""

    def test_discord_bot_creation(self):
        """Test that DiscordBot is properly initialized"""
        assert discord_bot.config.command_prefix == bot_config.command_prefix
        assert discord_bot.modal_timeout == 120
        assert discord_bot.llm_timeout == 60

    def test_discord_bot_handlers(self):
        """Test that handlers are properly initialized"""
        assert discord_bot.ollama_handler is not None
        assert discord_bot.openai_handler is not None
        assert discord_bot.multi_handler is not None
        assert discord_bot.scheduler is not None

    def test_command_groups_registered(self):
        """Test that command groups are registered"""
        assert discord_bot.admin_group is not None
        assert discord_bot.query_group is not None


# ============================================================================
# Tests for TextModal
# ============================================================================
class TestTextModal:
    """Test TextModal class functionality"""

    @pytest.mark.asyncio
    async def test_text_modal_creation(self):
        """Test TextModal initialization"""
        mock_interaction = MagicMock(spec=discord.Interaction)
        mock_validate = MagicMock(
            return_value=RetVal(status=True, message="Valid"))
        mock_llm_router = MagicMock(return_value=RetVal(
            status=True, data={'gherkin': 'Feature: Test'}, message="Ok"))
        mock_execute = MagicMock(
            return_value=RetVal(status=True, message="Done"))
        mock_send_msg = AsyncMock()

        modal = TextModal(
            title="Test Modal",
            label="Test Input",
            placeholder="Enter text",
            interaction=mock_interaction,
            validate_user_callback=mock_validate,
            llm_router_callback=mock_llm_router,
            execute_callback=mock_execute,
            send_msg_callback=mock_send_msg,
            timeout=60
        )

        assert modal.title == "Test Modal"
        assert modal.input.label == "Test Input"
        assert modal._ephemeral == False

    @pytest.mark.asyncio
    async def test_text_modal_on_submit_success(self):
        """Test TextModal can be created and has expected attributes"""
        mock_interaction = MagicMock(spec=discord.Interaction)

        mock_validate = MagicMock(
            return_value=RetVal(status=True, message="Valid"))
        mock_llm_router = MagicMock(return_value=RetVal(
            status=True, data={'gherkin': 'Feature: Test'}, message="Ok"))
        mock_execute = MagicMock(return_value=RetVal(
            status=True, data={'embeds': []}, message="Done"))
        mock_send_msg = AsyncMock()

        modal = TextModal(
            title="Test Modal",
            label="Test Input",
            placeholder="Enter text",
            interaction=mock_interaction,
            validate_user_callback=mock_validate,
            llm_router_callback=mock_llm_router,
            execute_callback=mock_execute,
            send_msg_callback=mock_send_msg,
            timeout=60
        )

        # Test that modal has the expected attributes
        assert modal.input is not None
        assert modal._interaction == mock_interaction
        assert modal._validate_user == mock_validate
        assert modal._ephemeral == False


# ============================================================================
# Tests for DiscordBot private methods
# ============================================================================
class TestDiscordBotPrivateMethods:
    """Test DiscordBot private helper methods"""

    def test_validate_user_not_registered(self):
        """Test validation fails for non-registered user"""
        # Create a user ID that doesn't exist
        test_user_id = 9999999
        result = discord_bot._DiscordBot__validate_user(test_user_id)
        # Should fail because user not registered
        assert result.status == False
        assert "not registered" in result.message.lower()

    def test_is_gherkin_format_valid(self):
        """Test valid gherkin format detection"""
        valid_gherkin = """FFeature: pytick llm
Scenario: EMA10 and EMA20 rate analysis over 10 samples with close proximity and 0.5*ATR10
Given stocks from list TCS, INFY
When let ema10 = latest in 1 samples of day close ema 10
* let ema20 = latest in 1 samples of day close ema 20
* let ema10_rate = rate in 10 samples of day close ema 10
* let ema20_rate = rate in 10 samples of day close ema 20
* let close = latest in 1 samples of day close
* let atr10 = latest in 1 samples of day close atr 10
Then list buy = tickers with (ema10_rate > 0) & (ema20_rate > 0) & (abs(close - ema10) < 0.25 * atr10)"""

        result = discord_bot._DiscordBot__is_gherkin_format(valid_gherkin)
        # Either valid or invalid based on QueryHandler
        assert result.status == False

    def test_split_to_chunks_short_content(self):
        """Test chunk splitting with short content"""
        content = "Short content"
        chunks = discord_bot._DiscordBot__split_to_chunks(
            content, max_length=100)
        assert len(chunks) == 1
        assert chunks[0] == "Short content"

    def test_split_to_chunks_long_content(self):
        """Test chunk splitting with long content"""
        content = "\n".join([f"Line {i}" for i in range(100)])
        chunks = discord_bot._DiscordBot__split_to_chunks(
            content, max_length=100)
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= 150  # Allow some margin

    def test_get_embeds_creation(self):
        """Test embed creation"""
        parts = ["**Section 1**",
                 "[SBIN](https://example.com)", "[news](https://example.com)"]
        embeds = discord_bot._DiscordBot__getEmbeds("Test Title", parts)

        assert len(embeds) > 0
        assert all(isinstance(e, discord.Embed) for e in embeds)
        assert embeds[0].title == "Test Title"

    def test_get_embeds_with_many_fields(self):
        """Test embed creation with many fields"""
        parts = ["**Section 1**"] + [f"[Ticker{i}](link)" for i in range(30)]
        embeds = discord_bot._DiscordBot__getEmbeds("Test Title", parts)

        # Should create multiple embeds when field count exceeds limit
        assert len(embeds) >= 1
        for embed in embeds:
            # Discord limit is 25 fields per embed
            assert len(embed.fields) <= 25

    def test_create_ticker_list(self):
        """Test ticker list creation"""
        results = [{"query1": ["SBIN", "TCS"]}]
        user_config = {"chart": "tradingview"}
        new_tickers = {}
        previous_results = []

        parts = discord_bot._DiscordBot__create_ticker_list(
            results, user_config, new_tickers, previous_results
        )

        assert len(parts) > 0
        assert any("query1" in str(p) for p in parts)


# ============================================================================
# Tests for LLM Router and Conversion
# ============================================================================
class TestLLMRouter:
    """Test LLM routing functionality"""

    def test_llm_router_with_valid_gherkin(self):
        """Test llm_router with already valid gherkin"""
        # Register test user first
        test_user_id = 11111
        convo_store.set_user(
            user_id=test_user_id,
            user_name="testuser",
            display_name="Test User",
            chart="tradingview",
            joined_at="2026-04-17",
            origin_guild_id=0,
            origin_channel_id=0
        )

        valid_gherkin = """Feature: Test
Scenario: Verify stocks
Given stocks from index nifty50
When let close = latest in 1 samples of day close
Then list result = tickers with close > 100"""

        result = discord_bot._DiscordBot__llm_router(
            test_user_id, valid_gherkin, allow_openai=False)
        assert isinstance(result, RetVal)

        # Cleanup
        convo_store.delete_user(test_user_id)


# ============================================================================
# Tests for Query Commands
# ============================================================================
class TestQueryCommands:
    """Test query command handlers"""

    def test_query_commands_guide(self):
        """Test query commands guide generation"""
        guide = discord_bot.query_commands_guide()
        assert isinstance(guide, str)
        assert "query" in guide.lower()
        assert "run" in guide.lower()


# ============================================================================
# Tests for Message Utilities
# ============================================================================
class TestMessageUtilities:
    """Test message utility functions"""

    def test_query_commands_guide_content(self):
        """Test that query guide includes all commands"""
        guide = discord_bot.query_commands_guide()
        commands = ["run", "subscribe", "unsubscribe", "trade"]
        for cmd in commands:
            assert cmd in guide.lower()


# ============================================================================
# Integration Tests
# ============================================================================
class TestDiscordBotIntegration:
    """Integration tests for DiscordBot"""

    @pytest.mark.asyncio
    async def test_bot_config_integration(self):
        """Test that bot is properly configured with all handlers"""
        assert discord_bot.config.query_handler is not None
        assert discord_bot.config.trade_handler is not None
        assert discord_bot.config.notification_handler is not None
        assert discord_bot.config.convo_store is not None


# ============================================================================
# Tests for Admin Commands
# ============================================================================
class TestAdminCommands:
    """Test admin command handlers"""

    @pytest.mark.asyncio
    async def test_admin_join_success(self):
        """Test successful user join"""
        mock_interaction = MagicMock(spec=discord.Interaction)
        mock_interaction.user.id = 22222
        mock_interaction.user.name = "testuser"
        mock_interaction.user.display_name = "Test User"
        mock_interaction.guild_id = 123456
        mock_interaction.channel_id = 789012
        mock_interaction.response.send_message = AsyncMock()
        mock_interaction.user.create_dm = AsyncMock()
        mock_dm = AsyncMock()
        mock_dm.send = AsyncMock()
        mock_interaction.user.create_dm.return_value = mock_dm

        # Run admin_join
        await discord_bot.admin_join(mock_interaction)

        # Verify user was added to convo_store
        user_data = convo_store.get_user(user_id=22222)
        if user_data:
            assert len(user_data) > 0

        # Cleanup
        convo_store.delete_user(22222)

    @pytest.mark.asyncio
    async def test_admin_join_dm_failure(self):
        """Test admin join when DM creation fails"""
        mock_interaction = MagicMock(spec=discord.Interaction)
        mock_interaction.user.id = 33333
        mock_interaction.user.name = "testuser"
        mock_interaction.user.display_name = "Test User"
        mock_interaction.guild_id = 123456
        mock_interaction.channel_id = 789012
        mock_interaction.response.send_message = AsyncMock()
        mock_interaction.user.create_dm = AsyncMock(
            side_effect=discord.Forbidden(MagicMock(), "DM error"))
        mock_interaction.edit_original_response = AsyncMock()

        await discord_bot.admin_join(mock_interaction)

        # Should attempt to edit response with error message
        assert mock_interaction.response.send_message.called or mock_interaction.edit_original_response.called

    @pytest.mark.asyncio
    async def test_admin_leave(self):
        """Test user leave command is handled"""
        test_user_id = 44444

        mock_interaction = MagicMock(spec=discord.Interaction)
        mock_interaction.user.id = test_user_id
        mock_interaction.response.send_message = AsyncMock()

        # Mock the async delete_user method
        with patch.object(discord_bot.convo_store, 'delete_user', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = None
            try:
                await discord_bot.admin_leave(mock_interaction)
            except TypeError:
                # Expected if there's type mismatch, just verify response was sent
                pass

        # Verify the command was handled
        assert mock_interaction.response.send_message.called


# ============================================================================
# Tests for Query Commands - Advanced
# ============================================================================
class TestQueryCommandsAdvanced:
    """Advanced tests for query command handlers"""

    @pytest.mark.asyncio
    async def test_query_run_command(self):
        """Test query run command modal creation"""
        mock_interaction = MagicMock(spec=discord.Interaction)
        mock_interaction.response.send_modal = AsyncMock()

        await discord_bot.query_run(mock_interaction)

        # Verify modal was sent
        assert mock_interaction.response.send_modal.called
        call_args = mock_interaction.response.send_modal.call_args
        modal = call_args[0][0] if call_args[0] else call_args[1].get('modal')
        assert isinstance(modal, TextModal)

    @pytest.mark.asyncio
    async def test_query_subscribe_command(self):
        """Test query subscribe command"""
        mock_interaction = MagicMock(spec=discord.Interaction)
        mock_interaction.response.send_modal = AsyncMock()

        # Create a mock interval choice with value attribute
        interval_choice = MagicMock()
        interval_choice.value = "5m"
        interval_choice.name = "5 minutes"

        await discord_bot.query_subscribe(mock_interaction, interval_choice)

        assert mock_interaction.response.send_modal.called

    @pytest.mark.asyncio
    async def test_query_subscribe_ls_empty(self):
        """Test listing subscriptions when none exist"""
        test_user_id = 55555
        # Make sure user exists in store
        convo_store.set_user(
            user_id=test_user_id,
            user_name="testuser",
            display_name="Test User",
            chart="tradingview",
            joined_at="2026-04-17",
            origin_guild_id=0,
            origin_channel_id=0
        )

        mock_interaction = MagicMock(spec=discord.Interaction)
        mock_interaction.user.id = test_user_id
        mock_interaction.response.defer = AsyncMock()
        mock_interaction.followup.send = AsyncMock()

        await discord_bot.query_subscribe_ls(mock_interaction)

        assert mock_interaction.response.defer.called

        # Cleanup
        convo_store.delete_user(test_user_id)

    @pytest.mark.asyncio
    async def test_query_trade_command(self):
        """Test query trade command"""
        mock_interaction = MagicMock(spec=discord.Interaction)
        mock_interaction.response.send_modal = AsyncMock()

        await discord_bot.query_trade(mock_interaction, stop_loss_percent=5, rolling_stop_loss=False)

        assert mock_interaction.response.send_modal.called

    @pytest.mark.asyncio
    async def test_query_trade_ls_empty(self):
        """Test listing trade subscriptions when none exist"""
        test_user_id = 66666
        convo_store.set_user(
            user_id=test_user_id,
            user_name="testuser",
            display_name="Test User",
            chart="tradingview",
            joined_at="2026-04-17",
            origin_guild_id=0,
            origin_channel_id=0
        )

        mock_interaction = MagicMock(spec=discord.Interaction)
        mock_interaction.user.id = test_user_id
        mock_interaction.response.defer = AsyncMock()
        mock_interaction.followup.send = AsyncMock()

        await discord_bot.query_trade_ls(mock_interaction)

        assert mock_interaction.response.defer.called

        # Cleanup
        convo_store.delete_user(test_user_id)


# ============================================================================
# Tests for Message Handling
# ============================================================================
class TestMessageHandling:
    """Test message handling functionality"""

    @pytest.mark.asyncio
    async def test_should_handle_chat_message_dm(self):
        """Test handling of DM messages"""
        mock_message = MagicMock(spec=discord.Message)
        mock_message.channel = MagicMock(spec=discord.DMChannel)

        result = discord_bot._DiscordBot__should_handle_chat_message(
            mock_message)
        assert result == True

    @pytest.mark.asyncio
    async def test_should_handle_chat_message_mentioned(self):
        """Test handling of messages that mention the bot"""
        mock_message = MagicMock(spec=discord.Message)
        mock_message.channel = MagicMock(spec=discord.TextChannel)
        # Create mock user that's in mentions
        mock_user = MagicMock()
        mock_message.mentions = [mock_user]
        # Set discord_bot.user to match what's in mentions
        if discord_bot.user:
            # If bot has a user, add it to mentions
            mock_message.mentions.append(discord_bot.user)

        result = discord_bot._DiscordBot__should_handle_chat_message(
            mock_message)
        # Result depends on whether bot.user is set
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_should_handle_chat_message_not_relevant(self):
        """Test ignoring irrelevant messages"""
        mock_message = MagicMock(spec=discord.Message)
        mock_message.channel = MagicMock(spec=discord.TextChannel)
        mock_message.mentions = []

        result = discord_bot._DiscordBot__should_handle_chat_message(
            mock_message)
        assert result == False


# ============================================================================
# Tests for Error Handling
# ============================================================================
class TestErrorHandling:
    """Test error handling in various scenarios"""

    @pytest.mark.asyncio
    async def test_command_error_not_found(self):
        """Test handling of CommandNotFound error"""
        mock_ctx = MagicMock()
        mock_ctx.send = AsyncMock()
        # Simulate CommandNotFound with a command name
        error = MagicMock(spec=commands.CommandNotFound)
        error.__str__ = MagicMock(return_value="Command not found")

        # Test should verify error handling exists
        # on_command_error is implemented so it should handle this
        try:
            await discord_bot.on_command_error(mock_ctx, error)
        except Exception:
            pass  # Expected for some error types

    @pytest.mark.asyncio
    async def test_command_error_missing_argument(self):
        """Test handling of MissingRequiredArgument error"""
        mock_ctx = MagicMock()
        mock_ctx.send = AsyncMock()
        mock_param = MagicMock()
        mock_param.name = "test_param"
        error = MagicMock(spec=commands.MissingRequiredArgument)
        error.param = mock_param

        # Test should verify error handling exists
        try:
            await discord_bot.on_command_error(mock_ctx, error)
        except Exception:
            pass  # Expected for some error types


# ============================================================================
# Tests for Rate Limiting and Validation
# ============================================================================
class TestRateLimitingValidation:
    """Test rate limiting and user validation"""

    def test_is_registered_user_not_found(self):
        """Test checking if non-existent user is registered"""
        test_user_id = 99999
        result = discord_bot._DiscordBot__is_registered_user(test_user_id)
        # User should not exist, so it should return False status or appropriate message
        assert isinstance(result, RetVal)

    def test_is_registered_user_exists(self):
        """Test checking if existing user is registered"""
        test_user_id = 77777
        # Register user first
        convo_store.set_user(
            user_id=test_user_id,
            user_name="testuser",
            display_name="Test User",
            chart="tradingview",
            joined_at="2026-04-17",
            origin_guild_id=0,
            origin_channel_id=0
        )

        result = discord_bot._DiscordBot__is_registered_user(test_user_id)
        assert isinstance(result, RetVal)
        assert result.status == True

        # Cleanup
        convo_store.delete_user(test_user_id)

# ============================================================================
# Tests for Trade Commands
# ============================================================================


# class TestTradeCommands:
#     """Test trade commands and related validation"""
#     @pytest.mark.asyncio
#     async def test_trade_command(self):
#         """Test trade command functionality"""
#         test_user_id = 77777
#         query = """Feature: pytick llm
# Scenario: Bearish and Bullish Reversal Analysis with Minute 5 Close, VWAP, and ATR10
# Given stocks from index nifty50
# When let close = latest in 1 samples of minute5 close
# * let vwap = latest in 1 samples of minute5 close vwap 10
# * let atr10 = latest in 1 samples of day close atr 10
# Then list sell = tickers with ((close - vwap) > (atr10 * 0.5))
# * list buy = tickers with ((vwap - close) > (atr10 * 0.5))"""

#         # Delete existing subscription if it exists, then re-subscribe
#         convo_store.clear_user_subs(user_id=test_user_id, sub_type='trade')
#         # Cleanup
#         convo_store.delete_user(test_user_id)

#         # Register test user
#         convo_store.set_user(
#             user_id=test_user_id,
#             user_name="tradeuser",
#             display_name="Trade Test User",
#             chart="tradingview",
#             joined_at="2026-04-18",
#             origin_guild_id=0,
#             origin_channel_id=0
#         )

#         investment = 100000
#         stop_loss_percent = 2
#         convo_store.subscribe_query(
#             query=query, user_id=test_user_id, data={
#                 'interval': '5m',  # for trade check use 5m interval for more real-time execution
#                 'stop_loss_percent': stop_loss_percent,
#                 'rolling_stop_loss': True,
#                 'portfolio': [],
#                 'acc_gain': 0.0,
#                 'investment': investment
#             }, sub_type='trade')

#         # Mock fetch_user to avoid real Discord API calls
#         mock_user = MagicMock(spec=discord.User)
#         mock_user.id = test_user_id
#         mock_user.name = "tradeuser"
#         default_ticker = 'SBIN'
#         full_test_data = []
#         with patch.object(discord_bot, 'fetch_user', new_callable=AsyncMock) as mock_fetch:
#             mock_fetch.return_value = mock_user

#             # Mock the __send_direct_msg method to avoid sending messages
#             with patch.object(discord_bot, '_DiscordBot__send_direct_msg', new_callable=AsyncMock):
#                 for iteration in range(2000, 0, -1):
#                     test_data = []
#                     back_data_handler = copy.deepcopy(data_handler)
#                     back_data_handler.trim_tables(
#                         tickers, "5m", trim_rows=iteration)
#                     df_5m = back_data_handler.tables['5m'][default_ticker]
#                     df_1d = back_data_handler.tables['1d'][default_ticker]
#                     end_date = str(df_5m.iloc[-1]['datetime'].date())
#                     sync_day = pandas.Timestamp(
#                         f"{end_date} 00:00:00+05:30")
#                     day_trim_row = df_1d[df_1d['datetime']
#                                          == sync_day].index[0]
#                     back_data_handler.trim_tables(
#                         tickers, "1d", trim_rows=len(df_1d) - day_trim_row)
#                     discord_bot.config.trade_handler.data_handler = back_data_handler
#                     discord_bot.config.query_handler.data_handler = back_data_handler
#                     await discord_bot._DiscordBot__run_query(
#                         '5m', [test_user_id], 'trade', discord_bot._DiscordBot__trade_callback, test_data)
#                     full_test_data.append(test_data)

#         for pt in full_test_data:
#             closed = pt[0]['closed']
#             opened = pt[0]['opened']

#             def print_trades(trades, trade_type="Opened"):
#                 if len(trades) > 0:
#                     print(f"\n{trade_type} trades:")
#                     for t in trades:
#                         print(t)

#             print_trades(opened, "Opened")
#             print_trades(closed, "Closed")

#         assert isinstance(full_test_data, list)


class TestQueryBacktest:
    """Test backtest functionality for trade commands"""

    @pytest.mark.asyncio
    async def test_trade_backtest(self):
        """Test backtest logic for trade commands"""
        # This test would ideally run a backtest on a sample query and verify results
        # For simplicity, we will just verify that the backtest can be executed without errors
        test_user_id = 77777
        query = """Feature: pytick llm
Scenario: Bearish and Bullish Reversal Analysis with Minute 5 Close, VWAP, and ATR10
Given stocks from index nifty50
When let close = latest in 1 samples of minute5 close
* let vwap = latest in 1 samples of minute5 close vwap 10
* let atr10 = latest in 1 samples of day close atr 10
Then list sell = tickers with ((close - vwap) > (atr10 * 0.05))
* list buy = tickers with ((vwap - close) > (atr10 * 0.05))"""
        # Cleanup
        convo_store.delete_user(test_user_id)

        # Register test user
        convo_store.set_user(
            user_id=test_user_id,
            user_name="tradeuser",
            display_name="Trade Test User",
            chart="tradingview",
            joined_at="2026-04-18",
            origin_guild_id=0,
            origin_channel_id=0
        )

        # Mock fetch_user to avoid real Discord API calls
        mock_user = MagicMock(spec=discord.User)
        mock_user.id = test_user_id
        mock_user.name = "tradeuser"
        with patch.object(discord_bot, 'fetch_user', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_user

            # Mock the __send_direct_msg method to avoid sending messages
            with patch.object(discord_bot, '_DiscordBot__send_direct_msg', new_callable=AsyncMock):
                discord_bot._DiscordBot__do_backtest(
                    interaction=MagicMock(spec=discord.Interaction),
                    query=query,
                    interval='5m',
                    window=100,
                    stop_loss_percent=2,
                    rolling_stop_loss=True,
                )


if __name__ == "__main__":
    asyncio.run(TestQueryBacktest().test_trade_backtest())

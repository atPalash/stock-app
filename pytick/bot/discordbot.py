from collections.abc import Callable
import asyncio
import copy
from datetime import datetime, tzinfo
import functools
import inspect
import json
import logging
from urllib.parse import quote_plus
from unittest.mock import MagicMock, Mock
from numpy.strings import title

import io
import trafilatura
import pytz
from attr import dataclass
import discord
from discord import app_commands
from discord.ext import commands
import pandas
from pydantic import BaseModel, typing
from pygooglenews import GoogleNews
import redis
from func_timeout import func_timeout, FunctionTimedOut
from ddgs import DDGS
from pytick.bot.utility import format_table
from pytick.utility.convo_store import ConvoStore
from pytick.query.trade import TradeHandler
from pytick.dataframe.notification import NotificationHandler
from pytick.llm.gherkin_agents.converter import converter_agent as gherkin_converter
from pytick.llm.gherkin_agents.router import router as gherkin_router
from pytick.llm.gherkin_agents.validator import validator_agent as gherkin_validator
from pytick.llm.common_agents.converter import converter_agent as common_converter
from pytick.llm.common_agents.validator import validator_agent as common_validator
from pytick.llm.common_agents.router import router as common_router
from pytick.llm.gherkin_agents.converter import converter_agent as gherkin_converter
from pytick.llm.gherkin_agents.validator import validator_agent as gherkin_validator
from pytick.llm.gherkin_agents.router import router as gherkin_router
from pytick.llm.classifier_agents.converter import converter_agent as classifier_converter
from pytick.llm.classifier_agents.validator import validator_agent as classifier_validator
from pytick.llm.search_agents.converter import converter_agent as search_converter
from pytick.llm.graph import Graph
from pytick.llm.multi_graph import MultiGraph
from pytick.query.query import QueryHandler
from pytick.scheduler.scheduler import Scheduler
from discord.app_commands import Range
from pytick.utility.utility import RetVal, clean_gherkin, get_logger

logger = get_logger(__file__, logging.DEBUG)


@dataclass(frozen=True)
class BotConfig:
    """Configuration parameters for the Discord bot during initialisation."""
    command_prefix: str
    token: str
    query_handler: QueryHandler
    notification_handler: NotificationHandler
    llm_convert_msg: str
    tz: str | tzinfo
    schedules: dict
    zerodha_df: pandas.DataFrame
    trading_view_url: str
    zerodha_url: str
    link_type: str
    backtest_iterations: int
    default_ticker: str
    convo_store: ConvoStore
    convo_ttl_seconds: int
    modal_timeout: int
    llm_timeout: int
    guild_id: int
    ollama_model: str
    openai_model: str
    llm_prompt: str
    retry_prompt: str
    joining_prompt: str
    disclaimer: str


INVISIBLE = "\u200b"


class TextModal(discord.ui.Modal):
    def __init__(
        self,
        title: str,
        label: str,
        placeholder: str,
        interaction: discord.Interaction,
        validate_user_callback: Callable[[int], RetVal],
        llm_router_callback: Callable[[int, str], RetVal],
        execute_callback: Callable[[str, discord.Interaction], RetVal],
        send_msg_callback: Callable[[discord.Interaction, str, discord.Embed, bool], None],
        timeout: int,
        ephemeral: bool = False,
    ):
        super().__init__(title=title, timeout=timeout)

        self.input = discord.ui.TextInput(
            label=label,
            placeholder=placeholder,
            style=discord.TextStyle.paragraph,
            max_length=4000,
            required=True,
        )
        self.add_item(self.input)  # ensure input is registered on the modal

        self._execute_callback = execute_callback
        self._validate_user = validate_user_callback
        self._llm_router_callback = llm_router_callback
        self._send_msg_callback = send_msg_callback
        self._ephemeral = ephemeral
        self._interaction = interaction
        self._submitted = False

    async def on_submit(self, interaction: discord.Interaction):
        try:
            self._submitted = True
            await interaction.response.defer(thinking=True)
            try:
                result = self._validate_user(interaction.user.id)
                if not result.status:
                    await self._send_msg_callback(interaction, content=result.message)
                    return

                result = self._llm_router_callback(
                    interaction.user.id, self.input.value)
                gherkin = result.data.get('gherkin', '')

                if not result.status or gherkin == '':
                    await self._send_msg_callback(interaction, content=result.message)
                    return

                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(
                    None, 
                    self._execute_callback, 
                    gherkin, 
                    interaction
                )

                if not result.status:
                    logger.warning(f"Failure: {gherkin}")
                    await self._send_msg_callback(interaction, content=f"{result.errors}")
                    return

                open_df = result.data.get('open', pandas.DataFrame())
                close_df = result.data.get('close', pandas.DataFrame())
                embeds = result.data.get("embeds", [])
                if len(embeds) > 0:
                    count = 0
                    for embed in result.data.get("embeds", []):
                        content = gherkin if count == 0 else ""
                        count += 1
                        await self._send_msg_callback(interaction, content=content, embed=embed)
                elif len(open_df) > 0 or len(close_df):
                    async def send_table_func(df: pandas.DataFrame, title):
                        columns = list(df.columns)
                        trades = df.to_dict(orient='records')
                        if len(trades) > 0:
                            # Split the list into chunks of 10
                            chunk_size = 5
                            chunks = [trades[i:i + chunk_size]
                                      for i in range(0, len(trades), chunk_size)]
                            for chunk in chunks:
                                table = format_table(chunk, columns)
                                await self._send_msg_callback(interaction, content=f"{title}:\n{table}")

                    async def send_csv_func(df: pandas.DataFrame, title):
                        with io.BytesIO() as binary_stream:
                            df = df.round(2)
                            df.to_csv(binary_stream, index=False,
                                      encoding='utf-8', float_format='%.2f')
                            binary_stream.seek(0)
                            discord_file = discord.File(
                                binary_stream, filename=f"{title}.csv")
                            await interaction.followup.send(f"**{title}**", file=discord_file)

                    await self._send_msg_callback(interaction, content=gherkin)
                    await send_csv_func(open_df, 'Open trades')
                    await send_csv_func(close_df, 'Closed trades')
                    await self._send_msg_callback(interaction, content=result.message)
                else:
                    await self._send_msg_callback(interaction, content=result.message)

            except Exception as e:
                logger.warning(f"Exception: {self.input.value}")
                await self._send_msg_callback(interaction, content=f"Error: {e}")
        except Exception as e:
            logger.warning(f"Failure: {e}")

    async def on_timeout(self):
        if self._submitted:
            return
        try:
            await self._send_msg_callback(
                self._interaction,
                content="⏰ This modal timed out. Please run the command again.",
                ephemeral=True
            )
        except Exception as e:
            logger.warning(f"Modal timeout notification failed: {e}")


class DiscordBot(commands.Bot):
    def __init__(self, config: BotConfig):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.dm_messages = True
        intents.guilds = True
        # Required to receive member update events (e.g., onboarding pending -> False)
        intents.members = True
        super().__init__(command_prefix=config.command_prefix, intents=intents)
        self.config = config
        self.modal_timeout = config.modal_timeout
        self.llm_timeout = config.llm_timeout
        self.convo_store = config.convo_store
        self.ollama_handler = Graph(
            system_prompt=config.llm_prompt,
            retry_prompt=config.retry_prompt,
            converter_agent=gherkin_converter,
            validator_agent=gherkin_validator,
            router_agent=gherkin_router,
            ollama_model=config.ollama_model)
        self.openai_handler = Graph(
            system_prompt=config.llm_prompt,
            retry_prompt=config.retry_prompt,
            converter_agent=gherkin_converter,
            validator_agent=gherkin_validator,
            router_agent=gherkin_router,
            openai_model=config.openai_model)

        classifier_system_prompt = f"""You are a classfier to route user instructions

CRITICAL INSTRUCTIONS:
1. You MUST respond with ONLY one of these VALID_WORKERS
2. Your response must be a single word, nothing else
3. Do NOT include any explanation, punctuation, or additional text
4. If unsure, respond with "default"
"""
        self.multi_handler = MultiGraph(
            classifier=Graph(
                id='classifier',
                system_prompt=classifier_system_prompt,
                retry_prompt='Retry classification, Note: there might be keywords which can help in classification',
                converter_agent=classifier_converter,
                validator_agent=classifier_validator,
                router_agent=common_router,
                ollama_model='llama3',
                openai_model=''),
            default=Graph(
                id='default',
                system_prompt='You are a chatbot to answer user query',
                retry_prompt='You are a chatbot to answer user query',
                converter_agent=common_converter,
                validator_agent=common_validator,
                router_agent=common_router,
                ollama_model='gemma3',
                openai_model=''),
            search=Graph(
                id='search',
                system_prompt='You are a chatbot which makes a web search for latest data and answer user query based on web content',
                retry_prompt='Retry to make a web search again for latest data and answer user query based on web content',
                converter_agent=search_converter,
                validator_agent=common_validator,
                router_agent=common_router,
                ollama_model='gemma3',
                openai_model=''))
        self.scheduler = Scheduler(config.tz, is_async=True)

        # set up command groups
        self.admin_group = app_commands.Group(
            name="admin", description="Admin related commands")
        self.admin_group.command(
            name="join", description="Join bot service")(self.admin_join)
        self.admin_group.command(
            name="leave", description="Leave bot service")(self.admin_leave)
        self.admin_group.command(
            name="help", description="Show help for admin commands")(self.help_doc)
        self.tree.add_command(self.admin_group)
        # query group for query related commands
        self.query_group = app_commands.Group(
            name="query", description="Query related commands")
        self.query_group.command(
            name="run", description="Run a query, AI will help you!")(self.query_run)
        self.query_group.command(
            name="subscribe", description="Subscribe to a query")(self.query_subscribe)
        self.query_group.command(
            name="subscribe_ls", description="List subscribed query")(self.query_subscribe_ls)
        self.query_group.command(
            name="unsubscribe", description="Unsubscribe to a query")(self.query_unsubscribe)
        self.query_group.command(
            name="backtest", description="Backtest a query")(self.query_bt)
        self.query_group.command(
            name="help", description="Show help for query commands")(self.help_doc)
        self.tree.add_command(self.query_group)

    def query_commands_guide(self) -> str:
        """Build a user-facing list of query slash commands dynamically."""
        lines = [
            "# 📊 Query commands guide",
            "",
            "Use these commands to run and manage your queries:",
            "",
        ]
        for cmd in self.query_group.commands:
            lines.append(
                f"**/{self.query_group.name} {cmd.name}** – {cmd.description}")
        return "\n".join(lines)

    async def run_async(self):
        async with self:
            await self.start(self.config.token)

    async def on_ready(self):
        logger.info(f'Logged in as {self.user}\nSubscribing to queries')
        self.__set_schedulers()

    async def on_member_update(self, before: discord.Member, after: discord.Member):
        # Membership screening/onboarding completed when pending flips True -> False.
        if after.flags.completed_onboarding:
            try:
                user_id = after.id
                dm = await after.create_dm()
                # Use configured joining prompt or provide a default welcome message
                joining_message = self.config.joining_prompt
                await dm.send(joining_message)

                if not self.convo_store.get_user(user_id):
                    # Register the user in the conversation store
                    self.convo_store.set_user(
                        user_id=user_id,
                        user_name=after.name,
                        display_name=after.display_name,
                        chart="tradingview",
                        joined_at=datetime.now().strftime("%Y-%m-%d"),
                        origin_guild_id=after.guild.id,
                        origin_channel_id=after.dm_channel.id
                    )
                    logger.info(
                        f"Onboarding completed for {after.id}-{after.display_name}")
                else:
                    logger.info(
                        f"Onboarding completed for existing {after.id}-{after.display_name}")
            except discord.Forbidden:
                # User has DMs closed or blocked the bot.
                logger.warning(
                    f"{after.id}-{after.display_name} has disabled dm")
            except Exception as e:
                logger.warning(
                    f"Error during onboarding for {after.id}-{after.display_name}: {e}")

    async def on_message(self, message: discord.Message):
        """Route normal chat messages to guidance replies in DM or when mentioned."""
        try:
            if message.author.bot:
                return

            if message.guild is not None:
                return

            ret = self.__validate_user(message.author.id)
            if not ret.status:
                await message.channel.send(ret.message)
                return
            # refer to getting-started channel for help
            await message.channel.send("Please use slash commands to interact with me. Refer <#1485674291037995128> for guidance.")
            return
            """ INTENTIONAL DEACTIVATION OF MESSAGE-BASED INTERACTION TO FOCUS ON SLASH COMMANDS
            content = (message.content or "").strip()
            if content == "" or content.startswith("/"):
                return

            # Extract replied-to message once for reuse
            replied_to = None
            if message.reference:
                try:
                    replied_to = message.reference.resolved
                except Exception as e:
                    logger.warning(
                        f"Failed to get replied message context: {e}")

            if not self.__should_handle_chat_message(message, replied_to):
                return

            # Build replied context from extracted message
            replied_content = ""
            if replied_to:
                replied_content = f"{replied_to.content}"

            # Clean mention so the LLM/input checks receive the actual user text.
            if self.user:
                content = content.replace(self.user.mention, "").strip()
            if content == "":
                await message.channel.send(self.query_commands_guide())
                return
            if content.startswith("/"):
                await message.channel.send("Use slash commands directly in the composer. Try `/query help`.")
                return

            # Combine replied context with current input
            # full_input = replied_content + content

            dm = await message.author.create_dm()
            async with dm.typing():
                replies = await asyncio.to_thread(
                    self.__build_chat_reply,
                    query=content,
                    replied_content=replied_content,
                    user_id=message.author.id,
                )
            for reply in replies:
                if isinstance(reply, discord.embeds.Embed):
                    await self.__send_direct_msg(user=message.author, embed=reply)
                if reply == "":
                    continue
                await self.__send_direct_msg(user=message.author, content=reply)
            """
        except Exception as e:
            logger.warning(f"Chat routing failed: {e}")
        finally:
            await self.process_commands(message)

    async def on_command_error(self, ctx, error):
        """Global command error handler.

        Ignore CommandNotFound (user typed a non-existent command). For other
        errors, log details and optionally notify the user.
        """
        # Common case: user typed an unknown command — ignore silently
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(f"Missing command: {error}")
            return

        # Missing required argument -> give helpful feedback
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument: {error.param.name}")
            return

        # For invocation errors, log the original exception
        if isinstance(error, commands.CommandInvokeError):
            logger.exception(
                f"Exception in command {ctx.command} invoked by {ctx.author}")
            # Optionally notify the user
            try:
                await ctx.send("An internal error occurred while executing the command.")
            except Exception:
                pass
            return

        # Fallback: log unexpected errors
        logger.exception(f"Unhandled command error: {error}")

    async def setup_hook(self):
        await self.tree.sync()  # Sync global commands first to ensure they are registered
        # TODO - consider syncing only to specific guilds during development for faster iteration
        logger.info(
            f"Commands after sync: {[cmd.name for cmd in self.tree.get_commands()]}")

    async def help_doc(self, interaction: discord.Interaction):
        """Return help content for a specific command."""
        await interaction.response.defer()
        try:
            group_name = interaction.data.get('name', '')
            for cmd in interaction.command.parent.commands:
                cmd_name = cmd.name
                if cmd_name == 'help':
                    continue
                cmd = getattr(self, f"{group_name}_{cmd_name}", None)
                doc = f"==={group_name}_{cmd_name} command===\n{inspect.getdoc(cmd)}"
                await self.__send_followup_msg(interaction=interaction, content=doc, ephemeral=False)
        except Exception:
            logger.warning(
                f"Failed to retrieve help documentation for command {interaction.name}")

    async def admin_join(self, interaction: discord.Interaction):
        """
        Handles joining request from user to join server and get bot services. The
        Bot will send helper to the user via direct message

        Usage:
            Typically invoked in response to a Discord slash command
            when a user wants to join server
        """
        await interaction.response.send_message("Sending you a direct message, bot conversation will take place in private messages.", ephemeral=True)
        # attempt DM
        try:
            joining_message = self.config.joining_prompt or (
                f"Hello! 👋 I'm your friendly bot, and I'm here to help with your queries.\n\n"
            )
            dm = await interaction.user.create_dm()
            await dm.send(joining_message)
        except Exception:
            await interaction.edit_original_response(content=(
                "I couldn't DM you. Please enable DMs from server members"
            ))
            return

        # store conversation state in Redis
        self.convo_store.set_user(user_id=interaction.user.id,
                                  user_name=interaction.user.name,
                                  display_name=interaction.user.display_name,
                                  chart="tradingview",
                                  joined_at=datetime.now().strftime("%Y-%m-%d"),
                                  origin_guild_id=interaction.guild_id,
                                  origin_channel_id=interaction.channel_id)

    async def admin_leave(self, interaction: discord.Interaction):
        """
        Handles leaving request from user to leave server and bot services. The
        Bot will remove any user data from database

        Usage:
            Typically invoked in response to a Discord slash command
            when a user wants to leave server
        """
        await interaction.response.send_message("Leaving conversation.", ephemeral=True)
        await self.convo_store.delete_user(interaction.user.id)

    async def query_run(self, interaction: discord.Interaction):
        """
        Handles the single run for a query via a Discord interaction.
        This function presents the user with a modal for query submission within Discord.
        It automatically applies AI enhancements to the query if applicable (up to 10 times per day),
        or accepts queries following the "Feature → Scenario → Given/When/Then" format.
        The modal verifies user access, routes the query through the relevant LLM handler,
        executes the query, and provides feedback or results to the user.
        Args:
            interaction (discord.Interaction): The Discord interaction object representing the user's action.
        Usage:
            Typically invoked in response to a Discord slash command.
        """
        def callback(code, interaction) -> RetVal:
            return self.__do_run(interaction=interaction, query=code, timeout=self.llm_timeout)

        modal = TextModal(title="🤖 Run query", label="Query",
                          placeholder="🤖 AI auto-fixes queries (10/day) ✨\n \
Or use: Feature → Scenario → Given/When/Then",
                          interaction=interaction,
                          timeout=self.modal_timeout,
                          validate_user_callback=self.__validate_user,
                          llm_router_callback=self.__llm_router,
                          execute_callback=callback,
                          send_msg_callback=self.__send_followup_msg,
                          ephemeral=False)
        await interaction.response.send_modal(modal)

    @app_commands.choices(interval=[
        app_commands.Choice(name="5 minutes", value="5m"),
        app_commands.Choice(name="15 minutes", value="15m"),
        app_commands.Choice(name="30 minutes", value="30m"),
        app_commands.Choice(name="1 hour", value="1h"),
        app_commands.Choice(name="1 day", value="1d"),
        app_commands.Choice(name="1 week", value="1wk"),
    ])
    @app_commands.describe(interval="Subscription interval")
    async def query_subscribe(self, interaction: discord.Interaction, interval: app_commands.Choice[str]):
        """
        Handles the subscription process for a query via a Discord interaction.
        This function presents the user with a modal for query submission within Discord.
        It automatically applies AI enhancements to the query if applicable (up to 10 times per day),
        or accepts queries following the "Feature → Scenario → Given/When/Then" format.
        The modal verifies user access, routes the query through the relevant LLM handler,
        executes the query, and provides feedback or results to the user.
        Args:
            interaction (discord.Interaction): The Discord interaction object representing the user's action.
            interval (str): The subscription interval or frequency specified by the user. Valid intervals
            are 5m, 15m, 30m, 1h, id, 1wk.
        Usage:
            Typically invoked in response to a Discord slash command
            when a user wants to subscribe to query results.
        """
        def callback(code, interaction) -> RetVal:
            try:
                self.convo_store.subscribe_query(
                    query=code, user_id=interaction.user.id, data={
                        'interval': interval.value,
                        'results': []})
                return RetVal(status=True, message='Subscribed')
            except Exception as e:
                return RetVal(status=False, errors=[str(e)], message='Unsuccessful subscription')
        modal = TextModal(title="🤖 Subscribe to query", label="Query",
                          placeholder="🤖 AI auto-fixes queries (10/day) ✨\n \
Or use: Feature → Scenario → Given/When/Then",
                          interaction=interaction,
                          timeout=self.modal_timeout,
                          validate_user_callback=self.__validate_user,
                          llm_router_callback=self.__llm_router,
                          execute_callback=callback,
                          send_msg_callback=self.__send_followup_msg,
                          ephemeral=False)
        await interaction.response.send_modal(modal)

    async def query_subscribe_ls(self, interaction: discord.Interaction):
        """
        Handles listing queries subscribed by user with it's interval via a Discord interaction.

        Usage:
            Typically invoked in response to a Discord slash command
            when a user wants to list subscribed queries
        """
        try:
            await interaction.response.defer()
            subscriptions = self.convo_store.get_user_subs(
                user_id=interaction.user.id)
            if len(subscriptions.keys()) == 0:
                await self.__send_followup_msg(interaction=interaction, content='No query subscribed', ephemeral=False)
                return
            for query, data in subscriptions.items():
                sub_data = json.load(data)
                interval = sub_data.get("interval", "")
                await self.__send_followup_msg(interaction=interaction, content=f'Query interval: {interval}\n', ephemeral=False)
                await self.__send_followup_msg(interaction=interaction, content=f'{query}\n', ephemeral=False)
        except Exception as e:
            await self.__send_followup_msg(interaction=interaction, content=f'Failure: {e}', ephemeral=False)
            logger.warning(f'Failure: {e}')

    async def query_unsubscribe(self, interaction: discord.Interaction):
        """
        Handles the un-subscription process for a query via a Discord interaction.
        This function presents the user with a modal for query submission within Discord.
        Unsubscription relies on user sending the exact query to unsubscribe.
        Args:
            interaction (discord.Interaction): The Discord interaction object representing the user's action.
        Usage:
            Typically invoked in response to a Discord slash command
            when a user wants to subscribe to query results.
        """
        def callback(code, interaction) -> RetVal:
            try:
                status = self.convo_store.unsubscribe_query(
                    query=code, user_id=interaction.user.id)
                if status:
                    return RetVal(status=True, message=f'Un-subscribed:\n{code} ')
                else:
                    return RetVal(status=True, message=f'Failed unsubscribe:\n{code}')
            except Exception as e:
                return RetVal(status=False, errors=[str(e)], message='error in unsubscribe')
        modal = TextModal(title="🤖 Un-subscribe from a query", label="Query",
                          placeholder="Enter the exact query to un-subscribe",
                          interaction=interaction,
                          timeout=self.modal_timeout,
                          validate_user_callback=self.__validate_user,
                          llm_router_callback=self.__gherkin_check_router,
                          execute_callback=callback,
                          send_msg_callback=self.__send_followup_msg,
                          ephemeral=False)
        await interaction.response.send_modal(modal)

    @app_commands.describe(window="Window size for backtesting (max 100)", stop_loss_percent="Percentage for setting stop loss")
    async def query_bt(self, interaction: discord.Interaction, window: Range[int, 1, 100], stop_loss_percent: int):
        """
        Handles execution of backtesting actions for a query via a Discord interaction.
        This function presents the user with a modal for query submission within Discord.
        It automatically applies AI enhancements to the query if applicable (up to 10 times per day),
        or accepts queries following the "Feature → Scenario → Given/When/Then" format.
        The modal verifies user access, routes the query through the relevant LLM handler,
        executes the query, and provides feedback or results to the user.
        Args:
            interaction (discord.Interaction): The Discord interaction object representing the user's action.
            interval (str): The time interval for the backtesting query.
            window (int): The window size for the backtesting query.
            stop_loss_percent (float): The percentage for setting stop loss in trading action. The stop loss
            will be rolling based on the latest price with the defined percentage as buffer. 
            For example, if the stop_loss_percent is 5 and the latest price is 100, the stop loss will be set at 95. 
            If the price goes up to 110, the stop loss will be adjusted to 104.5, which is 5% below the latest price. 
            This allows for dynamic risk management in trading based on market movements.
            rolling_stop_loss (bool): Whether to enable rolling stop loss. If True, the stop loss will adjust dynamically
            based on the latest price movements.
        Usage:
            Typically invoked in response to a Discord slash command
            when a user wants to subscribe to query results.
        """
        def callback(code, interaction) -> RetVal:
            return self.__do_backtest(interaction=interaction, query=code,
                                      window=window, stop_loss_percent=stop_loss_percent)

        modal = TextModal(title="🤖 Set backtest on query", label="Query",
                          placeholder="🤖 AI auto-fixes queries (10/day) ✨\n \
Or use: Feature → Scenario → Given/When/Then",
                          interaction=interaction,
                          timeout=self.modal_timeout,
                          validate_user_callback=self.__validate_user,
                          llm_router_callback=self.__llm_router,
                          execute_callback=callback,
                          send_msg_callback=self.__send_followup_msg,
                          ephemeral=False)
        await interaction.response.send_modal(modal)

    def __validate_user(self, user_id: int) -> RetVal:
        """Call LLM to generate a short guidance message directing user to configured commands.
        Returns the message to send.
        """
        # rate limiting checks
        try:
            registration = self.__is_registered_user(user_id=user_id)
            if not registration.status:
                return registration
            per_count = self.convo_store.incr_rate(user_id)
            if per_count > 1:
                return RetVal(status=False, message="You're sending requests too quickly — please slow down.")
            return RetVal(status=True, message="Ok")
        except Exception as e:
            logger.warning(f"{e}")
            return RetVal(status=False, message=f"{e}", errors=[str(e)])

    def __is_registered_user(self, user_id: int) -> RetVal:
        """Check whether the user has joined the bot service."""
        user_exists = len(self.convo_store.get_user(
            user_id=user_id).keys()) == 0
        if user_exists:
            return RetVal(status=False, message="You're not registered. send /admin join from server")
        return RetVal(status=True, message="Ok")

    def __llm_router(self, user_id: int, input: str, allow_openai=False) -> RetVal:
        """Call LLM to generate a short guidance message directing user to configured commands.
        Returns the message to send.
        """
        # rate limiting checks
        try:
            result = self.__is_gherkin_format(input=input)
            query = result.data['gherkin']
            # Already in gherkin format, no need to convert
            if result.status:
                return RetVal(status=True, message='Query valid', data={'gherkin': query})

            query = clean_gherkin(input)

            # Will send result from either else timeout
            ret = self.__do_llm_conversion(
                llm_handler=self.ollama_handler, query=query)
            if allow_openai and not ret.status:
                daily_count = self.convo_store.get_daily_llm(user_id)
                if daily_count > 10:
                    return RetVal(status=False, message=f"🚫 Limit reached: {daily_count} premium guided messages used today. 🤖 Free AI is still here.")
                self.convo_store.incr_daily_llm(
                    user_id=user_id)
                logger.info(f'{user_id} used premium for {query}')
                ret = self.__do_llm_conversion(
                    llm_handler=self.openai_handler, query=query)
            return ret
        except Exception as e:
            logger.warning(f"{e}")
            return RetVal(status=False, message=f"{e}", errors=[str(e)])

    def __do_llm_conversion(self, llm_handler, query) -> RetVal:
        llm_result = ""
        try:
            # First call local ollama
            llm_result = func_timeout(
                self.llm_timeout,
                llm_handler.run,
                args=(query,)
            )
            llm_result = clean_gherkin(llm_result)
            # logger.info(
            #     f'{query} converted by {llm_handler.llm} to gherkin')
            if 'Feature' in llm_result:
                return RetVal(status=True, data={"gherkin": llm_result}, message=f'{llm_handler.llm} converted gherkin')
            return RetVal(status=False, message=f'Conversion failed: {query} \n{llm_result}')
        except FunctionTimedOut:
            logger.warning(
                f"{llm_handler} conversion timed out: {query}")
            return RetVal(status=False, message=f"⏰ AI conversion timed out for {query}", errors=["Timeout"])

    def __gherkin_check_router(self, _user_id: int, input: str) -> RetVal:
        """Check valid gherkin.
        """
        return self.__is_gherkin_format(input=input)

    def __set_schedulers(self):
        '''Set up periodic jobs for each subscription interval defined in the configuration.'''
        async def subscribe_handler(interval):
            """Async wrapper for _sub_handler to ensure proper coroutine handling."""
            await self.do_sub_run(interval=interval)

        self.scheduler.start()  # Start the scheduler before adding jobs
        for interval, params in self.config.schedules.items():
            try:
                self.scheduler.add_periodic_job(
                    func=functools.partial(
                        subscribe_handler, interval=interval),
                    params=params,
                    job_id=f"discord_subscription_job_{interval}")
            except Exception as e:
                logger.error(
                    f"Error setting up scheduler for interval {interval}: {e}")

    def __do_run(self, interaction: discord.Interaction, query: str, timeout: int, previous_results: list = []) -> RetVal:
        try:
            try:
                success, results, errors, _ = func_timeout(
                    timeout,
                    self.config.query_handler.get_gherkin_result,
                    args=(query,)
                )
            except FunctionTimedOut:
                logger.warning(f"Timeout: {query}")
                return RetVal(status=False, message=f"⏰ Cannot complete {input} within {timeout}s", errors=["Timeout"])

            # success, results, errors, _ = self.config.query_handler.get_gherkin_result(gherkin_str=query)
            title = query.splitlines()[1].split(
                ":", 1)[1].strip() if query else "Results"
            if len(title) > 20:
                title = f"{title[:20]}..."
            if not success:
                msg = f"Exception during query execution: {errors}"
                logger.warning(msg)
                return RetVal(status=False, message=msg, errors=[msg])
                # raise Exception(errors)

            user_config = self.convo_store.get_user(interaction.user.id)
            # fetch new tickers for qid
            new_tickers = {}
            for i in range(len(results)):
                for qid, tickers in results[i].items():
                    prev_tickers = previous_results[i].get(
                        qid, []) if i < len(previous_results) else []
                    new_tickers[i] = {
                        qid: list(set(tickers) - set(prev_tickers))}

            parts = self.__create_ticker_list(
                results, user_config, new_tickers, previous_results)
            return RetVal(status=True, message='check tickers', data={"results": results, "embeds": self.__getEmbeds(title, parts)}, errors=errors)
        except Exception as e:
            # msg = f"Exception during execution: {e}"
            logger.warning(f"{e}")
            raise e

    def __do_backtest(self, interaction: discord.Interaction, query: str, window: int, stop_loss_percent: int) -> RetVal:
        try:
            trade_handler = TradeHandler()

            def backtest_func():
                for itr in range(window, 0, -1):
                    bt_query_handler = copy.deepcopy(self.config.query_handler)
                    bt_query_handler.get_backtest_result(query=query, trade_handler=trade_handler,
                                                         window=itr, stop_loss_percent=stop_loss_percent)
            func_timeout(
                self.modal_timeout,
                backtest_func,
            )
            open_trades_count = len(trade_handler.open_df)
            closed_trades_count = len(trade_handler.close_df)
            total_rr = round(trade_handler.close_df['rmulti'].sum(
            ) + trade_handler.open_df['rmulti'].sum())
            return RetVal(status=True, data={"open": trade_handler.open_df, "close": trade_handler.close_df},
                          message=f"Trade summary: {open_trades_count} open and {closed_trades_count} closed trades with net risk ratio {total_rr}")

        except FunctionTimedOut:
            logger.warning(f"Backtest timeout: {query}")
            return RetVal(status=False, message=f"⏰ Cannot complete backtest for {input} within {self.llm_timeout}s", errors=["Timeout"])
        except Exception as e:
            logger.warning(f"{e}")
            raise e

    def __create_ticker_list(self, results: dict, user_config: dict, new_tickers: dict, previous_results: list) -> list[str]:
        parts = []
        for i in range(len(results)):
            point = results[i]
            for qid, tickers in point.items():
                parts.append(f"**{qid}**")
                chart_type = user_config.get("chart", "tradingview")
                corporate_actions = self.config.notification_handler.get_corporate_actions_dfs(
                    tickers=tickers)
                for t in tickers:
                    try:
                        # default to tradingview chart
                        chart_link = f"[{t}]({self.config.trading_view_url}{t})"
                        if chart_type == "zerodha":
                            token = self.config.zerodha_df.query(
                                f"tradingsymbol == '{t}' and exchange == 'NSE'")['instrument_token'].iloc[0]
                            chart_link = f"[{t}]({self.config.zerodha_url}{t}/{token})"
                        if chart_type == "tradingview" and any(c in t for c in ['-', '&']):
                            edited_t = t.replace(
                                '-', '_').replace('&', '_')
                            chart_link = f"[{t}]({self.config.trading_view_url}{edited_t})"
                        ticker_action = corporate_actions.get(t, None)
                        corporate_action_link = ""
                        if ticker_action is not None and not ticker_action.empty:
                            recent_action = ticker_action.tail(
                                1)['file'].values[0]
                            corporate_action_link = f"[action]({recent_action})"
                        news_link = f"[news](https://www.google.com/finance/quote/{t}:NSE)"
                        changed = ""
                        if len(new_tickers) > 0 and len(previous_results) > 0:
                            changed = "🟢" if t in new_tickers[i][qid] and len(
                                previous_results) > 0 else ""
                        ticker_clickables = [
                            chart_link, news_link, corporate_action_link, changed]
                        parts.append(' '.join(ticker_clickables))
                    except Exception as e:
                        parts.append(f"[{t}]")
                        logger.warning(f"Exception {t}: {e}")
        return parts

    async def do_sub_run(self, interval: str):
        """Run scheduler job for subscription. This is used to set tables for subscription
        queries based on interval.
        """
        await self.__run_query(interval, self.convo_store.get_all_user_sub_ids(), 'subs', self.__sub_logic)
        # await self.__run_query(interval, self.convo_store.get_all_user_sub_ids(sub_type='trade'), 'trade', self.__trade_callback)

    async def __run_query(self, interval, user_ids, sub_type, callback, test_data=[]):
        for uid in user_ids:
            user = await self.fetch_user(uid)
            user_interaction = Mock(spec=discord.Interaction)
            user_interaction.user = user
            subscribed_queries = self.convo_store.get_user_subs(
                user_id=user.id, sub_type=sub_type)
            for sub, data in subscribed_queries.items():
                sub_data = json.loads(data)
                sub_interval = sub_data.get("interval", "")
                previous_results = sub_data.get("results", [])
                if sub_interval == interval:
                    result = self.__do_run(
                        interaction=user_interaction,
                        query=sub,
                        timeout=self.llm_timeout,
                        previous_results=previous_results)
                    if not result.status:
                        logger.warning(
                            f"Failure interval {sub_type} {sub_interval}: {sub}")
                        await self.__send_direct_msg(user=user, content=f"{result.errors}")
                        return
                    await callback(user=user, query=sub, db_data=sub_data, result=result)

    async def __sub_logic(self, user, query, db_data, result):
        current_results = result.data.get('results', [])
        previous_results = db_data.get("results", [])
        if previous_results != current_results:
            db_data['results'] = current_results
            self.convo_store.subscribe_query(
                user_id=user.id, query=query, data=db_data, sub_type='subs')

            if not self.__has_tickers(current_results):
                # logger.info(f"No tickers found for {query}, skipping")
                return

            count = 0
            for embed in result.data.get("embeds", []):
                content = query if count == 0 else ""
                count += 1
                await self.__send_direct_msg(user=user, content=content, embed=embed)

    def __has_tickers(self, result: list[dict]) -> bool:
        for val in result:
            for qid, tickers in val.items():
                if len(tickers) > 0:
                    return True
        return False

    def __getEmbeds(self, title: str, parts: list[str]) -> list[discord.Embed]:
        try:
            def get_new_embed(title):
                # Add disclaimer to footer, with time
                footer_tz = pytz.timezone(
                    self.config.tz) if isinstance(self.config.tz, str) else self.config.tz
                embed_footer_text = f"{self.config.disclaimer}\n{datetime.now(tz=footer_tz):%Y-%m-%d %H:%M:%S}"
                embed = discord.Embed(
                    title=title, color=discord.Color.blurple())
                embed.set_footer(text=embed_footer_text)
                return embed

            emdbeds = []
            current_section = ""
            field_count = 0
            embed = get_new_embed(title=title)
            for part in parts:
                # Handle section headers
                if part.startswith("**") or part.strip() == "":
                    if part.strip() != "":
                        current_section = part.replace('*', '')
                        embed.add_field(name=current_section,
                                        value="⎯" * 20, inline=False)
                        field_count += 1
                    continue

                # Add ticker with all its links
                if part.strip():
                    # Use zero-width space for empty name to group under section
                    embed.add_field(name="​", value=part, inline=False)
                    field_count += 1

                # Send when embed gets too large (Discord limit is 25 fields)
                if field_count >= 20:
                    emdbeds.append(embed)
                    field_count = 0
                    embed = get_new_embed(title=f"{title} (cont.)")
                    if current_section:
                        embed.add_field(name=current_section,
                                        value="⎯" * 20, inline=False)
                    field_count = 1 if current_section else 0

            # Send final embed if it has fields
            if field_count > 0:
                emdbeds.append(embed)
            return emdbeds
        except Exception as e:
            logger.warning(e)
            raise e

    def __is_gherkin_format(self, input: str) -> RetVal:
        """Pre-check to extract gherkin text from reply or arguments.
        """
        try:
            clean_input = clean_gherkin(input)
            is_valid, _, errors = QueryHandler.parse_gherkin(clean_input)
            if not is_valid:
                return RetVal(status=False, data={"gherkin": ""}, message=f'Invalid query {input}', errors=errors)
        except Exception as e:
            logger.warning(f"{e}")
            return RetVal(status=False, errors=[e], message=f'Invalid query {e}')
        return RetVal(status=True, data={"gherkin": clean_input}, errors=[], message='valid gherkin')

    async def __send_discord_msg(self, interaction: discord.Interaction = None, user: discord.user = None, content: str = "", embed: discord.Embed = None, ephemeral=False):
        try:
            safe_chunks = self.__split_to_chunks(content=content)
            if interaction:
                for chunk in safe_chunks:
                    if chunk != "":
                        await interaction.followup.send(content=f"{chunk}", ephemeral=ephemeral)
                if embed:
                    await interaction.followup.send(embed=embed, ephemeral=ephemeral)
            if user:
                for chunk in safe_chunks:
                    if chunk != "":
                        await user.send(content=f"{chunk}")
                if embed:
                    await user.send(embed=embed)
        except Exception as e:
            logger.warning(f"Failure: cannot send message to user")

    async def __send_followup_msg(self, interaction: discord.Interaction, content: str = "", embed: discord.Embed = None, ephemeral=False):
        """Helper to send follow-up messages, ensuring we catch any exceptions to avoid unhandled errors."""
        await self.__send_discord_msg(
            interaction=interaction, content=content, embed=embed, ephemeral=ephemeral)

    async def __send_direct_msg(self, user: discord.user, content: str = "", embed: discord.Embed = None):
        """Helper to send direct messages, ensuring we catch any exceptions to avoid unhandled errors."""
        await self.__send_discord_msg(user=user, content=content, embed=embed)

    def __split_to_chunks(self, content: str, max_length=1900) -> list[str]:
        # Split into lines for clean breaks
        lines = content.split('\n')
        chunks = []
        current_chunk = []

        for line in lines:
            test_chunk = '\n'.join(current_chunk + [line])
            if len(test_chunk) > max_length:
                if current_chunk:
                    chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
            else:
                current_chunk.append(line)

        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        return chunks

    def __should_handle_chat_message(self, message: discord.Message, replied_to: discord.Message = None) -> bool:
        """Only handle DM chats, guild messages mentioning the bot, or replies to the bot."""
        if isinstance(message.channel, discord.DMChannel):
            return True
        if self.user and self.user in message.mentions:
            return True
        # Check if this is a reply to the bot's message
        if replied_to and replied_to.author.id == self.user.id:
            return True
        return False

    def __build_chat_reply(self, query: str, replied_content: str, user_id: int) -> list:
        """Build a guidance-first chat reply for non-command conversations."""
        try:
            return func_timeout(10, self.__build_chat_reply_impl, args=(query, replied_content, user_id))
        except FunctionTimedOut:
            logger.warning(f"{user_id} Chat reply timed out for {query}")
            return self.__make_chat_reply("I'm thinking too slow on that one. Try `/query run` for quick results.")

    def __build_chat_reply_impl(self, query: str, replied_content: str, user_id) -> list:
        """Build user message reply"""

        # # 1. First try to convert to valid gherkin query
        # ret = self.__do_llm_conversion(
        #     llm_handler=self.ollama_handler, query=input)
        # gherkin = ret.data.get('gherkin', '')
        # if ret.status and gherkin != '':
        #     return [gherkin, self.config]

        # 1. Check if the replied content is valid gherkin, run the query
        if replied_content != "":
            result = self.__is_gherkin_format(input=replied_content)
            if result.status:
                result = self.__llm_router(user_id=user_id,
                                           input=f"{replied_content}\n {query}", allow_openai=False)
                gherkin = result.data.get('gherkin', '')
                if not result.status or gherkin == '':
                    return [f'Failure: {query}\n{result.errors}']
                result = self.__do_run(MagicMock(user=MagicMock(id=user_id)),
                                       query=gherkin, timeout=self.llm_timeout, previous_results=[])
                if not result.status:
                    logger.warning(f"Failure: {gherkin}\n")
                    return [f'Failure: {query}\n{result.errors}']
                embeds = result.data.get("embeds", [])
                return [gherkin, *embeds]

        # On failure proceed as normal chat
        reply = self.multi_handler.run(f"{query}")
        return self.__make_chat_reply(reply)

    def __make_chat_reply(self, *contents) -> list:
        greeting = "Hello! 👋 I'm your friendly bot, and I'm here to help with stock queries. Check my capabilities in `/admin join`\n"
        ai_generated = "⚠️ Notice: This response includes AI-generated data. It may be inaccurate or incomplete\n"

        return [greeting, ai_generated, *contents]

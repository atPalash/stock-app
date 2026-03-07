from collections.abc import Callable
from datetime import datetime, tzinfo
import functools
import inspect
import json
import logging
from unittest.mock import Mock
from attr import dataclass
import discord
from discord import app_commands
from discord.ext import commands
import pandas
from pydantic import BaseModel, typing
import redis
from func_timeout import func_timeout, FunctionTimedOut
from pytick.bot.convo_store import ConvoStore
from pytick.bot.utility import get_user_ids
from pytick.llm.graph import Graph
from pytick.query.query import QueryHandler
from pytick.scheduler.scheduler import Scheduler
from pytick.utility.utility import clean_gherkin, get_logger
from collections.abc import Callable

logger = get_logger(__file__, logging.DEBUG)


@dataclass(frozen=True)
class BotConfig:
    """Configuration parameters for the Discord bot during initialisation."""
    command_prefix: str
    token: str
    query_handler: object
    notification_handler: object
    llm_convert_msg: str
    tz: tzinfo
    schedules: dict
    users_config_path: str
    zerodha_df: pandas.DataFrame
    trading_view_url: str
    zerodha_url: str
    link_type: str
    backtest_iterations: int
    default_ticker: str
    redis_url: str
    convo_ttl_seconds: int
    guild_id: int
    llm_prompt: str


class RetVal(BaseModel):
    status: bool = False
    message: str
    errors: list[str] = []
    data: dict = {}


INVISIBLE = "\u200b"


class TextModal(discord.ui.Modal):
    def __init__(
        self,
        title: str,
        label: str,
        placeholder: str,
        validate_user_callback: Callable[[int], RetVal],
        llm_router_callback: Callable[[int, str], RetVal],
        execute_callback: Callable[[str, discord.Interaction], RetVal],
        send_msg_callback: Callable[[discord.Interaction, str, discord.Embed, bool], None],
        timeout: int = 20,
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

    async def on_submit(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(thinking=True)
            try:
                result = self._validate_user(interaction.user.id)
                if not result.status:
                    await self._send_msg_callback(interaction, content=result.message)
                    return

                result = self._llm_router_callback(
                    interaction.user.id, self.input.value, self.timeout)
                gherkin = result.data.get('gherkin', '')
                if not result.status or gherkin == '':
                    await self._send_msg_callback(interaction, content=result.message)
                    return

                result = self._execute_callback(gherkin, interaction)
                if not result.status:
                    logger.warning(f"Failure: {gherkin}")
                    await self._send_msg_callback(interaction, content=f"{result.errors}")
                    return

                embeds = result.data.get("embeds", [])
                if len(embeds) > 0:
                    count = 0
                    for embed in result.data.get("embeds", []):
                        content = gherkin if count == 0 else ""
                        count += 1
                        await self._send_msg_callback(interaction, content=content, embed=embed)
                else:
                    await self._send_msg_callback(interaction, content=result.message)
            except Exception as e:
                logger.exception(f"Exception: {self.input.value}")
                await self._send_msg_callback(interaction, content=f"Error: {e}")
        except Exception as e:
            logger.warning(f"Failure: {e}")


class DiscordBot(commands.Bot):
    def __init__(self, config: BotConfig):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.dm_messages = True
        intents.guilds = True
        super().__init__(command_prefix=config.command_prefix, intents=intents)
        self.config = config
        self.users_config_path = config.users_config_path
        self.llm_handler = Graph(system_prompt=config.llm_prompt)
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
            name="subscribe_ls", description="List subscribed querie")(self.query_subscribe_ls)
        self.query_group.command(
            name="unsubscribe", description="Unsubscribe to a query")(self.query_unsubscribe)
        self.query_group.command(
            name="help", description="Show help for query commands")(self.help_doc)
        self.tree.add_command(self.query_group)

    async def run_async(self):
        redis_url = redis.from_url(
            self.config.redis_url, encoding="utf-8", decode_responses=True)
        self.convo_store = ConvoStore(redis_url)
        async with self:
            await self.start(self.config.token)

    async def on_ready(self):
        logger.info(f'Logged in as {self.user}\nSubscribing to queries')
        self.__set_schedulers()
        # Send hello message to all users on bot alive
        try:
            user_ids = []
            # List all user config files
            user_ids = get_user_ids(self.users_config_path)
            for uid in user_ids:
                user = await self.fetch_user(int(uid))
                try:
                    await user.send('Hello! 👋 The bot is now alive.')
                except Exception as e:
                    logger.warning(f"Could not send hello to user {uid}: {e}")
        except Exception as e:
            logger.warning(f"Exception sending hello messages: {e}")

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
            joining_message = f"Hello! 👋 I'm your friendly bot here to assist you.\n\n"
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
            return self.__do_run(interaction=interaction, query=code)

        modal = TextModal(title="🤖 Run query", label="Query",
                          placeholder="🤖 AI auto-fixes queries (10/day) ✨\n \
Or use: Feature → Scenario → Given/When/Then",
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
                    query=code, user_id=interaction.user.id, interval=interval.value)
                return RetVal(status=True, message='Subscribed')
            except Exception as e:
                return RetVal(status=False, errors=[str(e)], message='Unsuccessful subscription')
        modal = TextModal(title="🤖 Subscribe to query", label="Query",
                          placeholder="🤖 AI auto-fixes queries (10/day) ✨\n \
Or use: Feature → Scenario → Given/When/Then",
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
            fixed = []
            separator = '----------'
            for query, interval in subscriptions.items():
                fixed.append(f'Query interval: {interval}\n')
                fixed.append(f'{query}\n')
                fixed.append(separator)
            await self.__send_followup_msg(interaction=interaction, content='\n'.join(fixed), ephemeral=False)
        except Exception as e:
            await self.__send_followup_msg(interaction=interaction, content='Failure: {e}', ephemeral=False)
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
                          validate_user_callback=self.__validate_user,
                          llm_router_callback=self.__gherkin_check_router,
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
            user_exists = len(self.convo_store.get_user(
                user_id=user_id).keys()) == 0
            if user_exists:
                return RetVal(status=False, message="You're not registered. send /admin join from server")
            per_count = self.convo_store.incr_rate(user_id)
            if per_count > 1:
                return RetVal(status=False, message="You're sending requests too quickly — please slow down.")
            daily_count = self.convo_store.get_daily_llm(user_id)
            if daily_count > 100:
                return RetVal(status=False, message="You've reached the daily limit for guided messages. Please try again tomorrow.")
            return RetVal(status=True, message="Ok")
        except Exception as e:
            logger.warning(f"{e}")
            return RetVal(status=False, message=f"{e}", errors=[str(e)])

    def __llm_router(self, user_id: int, input: str, timeout: int) -> RetVal:
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
            try:
                # Call LLM to convert to gherkin
                # global daily count for llm usage
                self.convo_store.incr_daily_llm(user_id=user_id)
                llm_converted_input = func_timeout(
                    timeout,
                    self.llm_handler.run,
                    args=(query,)
                )
                return RetVal(status=True, data={"gherkin": llm_converted_input}, message='llm converted gherkin')
            except FunctionTimedOut:
                logger.warning(f"LLM conversion timed out: {query}")
                return RetVal(status=False, message=f"⏰ AI conversion timed out for {query}", errors=["Timeout"])
        except Exception as e:
            logger.warning(f"{e}")
            return RetVal(status=False, message=f"{e}", errors=[str(e)])

    def __gherkin_check_router(self, _user_id: int, input: str, _timeout: int) -> RetVal:
        """Check valid gherkin.
        """
        return self.__is_gherkin_format(input=input)

    def __set_schedulers(self):
        '''Set up periodic jobs for each subscription interval defined in the configuration.'''
        async def subscribe_handler(interval):
            """Async wrapper for _sub_handler to ensure proper coroutine handling."""
            await self.__do_sub_run(interval=interval)

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

    def __do_run(self, interaction: discord.Interaction, query: str, previous_results: list = [], timeout=20) -> RetVal:
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
                raise Exception(errors)

            user_config = self.convo_store.get_user(interaction.user.id)
            # fetch new tickers for qid
            new_tickers = {}
            for i in range(len(results)):
                for qid, tickers in results[i].items():
                    prev_tickers = previous_results[i].get(
                        qid, []) if i < len(previous_results) else []
                    new_tickers[i] = {
                        qid: list(set(tickers) - set(prev_tickers))}

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
                            changed = "🟢" if t in new_tickers[i][qid] and len(
                                previous_results) > 0 else ""
                            ticker_clickables = [
                                chart_link, news_link, corporate_action_link, changed]
                            parts.append(' '.join(ticker_clickables))
                        except Exception as e:
                            parts.append(f"[{t}]")
                            logger.warning(f"Exception {t}: {e}")
            return RetVal(status=True, message='check tickers', data={"results": results, "embeds": self.__getEmbeds(title, parts)}, errors=errors)
        except Exception as e:
            # msg = f"Exception during execution: {e}"
            logger.warning(f"{e}")
            raise e

    async def __do_sub_run(self, interval: int):
        """Run scheduler job for subscription. This is used to set tables for subscription
        queries based on interval. 
        """
        user_ids = self.convo_store.get_all_user_sub_ids()
        for uid in user_ids:
            user = await self.fetch_user(uid)
            user_interaction = Mock(spec=discord.Interaction)
            user_interaction.user = user
            subscribed_queries = self.convo_store.get_user_subs(
                user_id=user.id)
            for sub, sub_interval in subscribed_queries.items():
                if sub_interval == interval:
                    result = self.__do_run(
                        interaction=user_interaction, query=sub)
                    if not result.status:
                        logger.warning(
                            f"Failure interval {sub_interval}: {sub}")
                        await self.__send_direct_msg(user=user, content=f"{result.errors}")
                        return
                    count = 0
                    for embed in result.data.get("embeds", []):
                        content = sub if count == 0 else ""
                        count += 1
                        await self.__send_direct_msg(user=user, content=content, embed=embed)

    def __getEmbeds(self, title: str, parts: list[str]) -> list[discord.Embed]:
        try:
            emdbeds = []
            current_section = ""
            field_count = 0
            embed_title = title
            embed = discord.Embed(
                title=embed_title, color=discord.Color.blurple())
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
                    embed = discord.Embed(
                        title=embed_title, color=discord.Color.blurple())
                    field_count = 0
                    embed_title = f"{title} (cont.)"
                    embed = discord.Embed(
                        title=embed_title, color=discord.Color.blurple())
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
        return RetVal(status=True, data={"gherkin": clean_input}, errors=[], message='invalid gherkin')

    async def __send_discord_msg(self, interaction: discord.Interaction = None, user: discord.user = None, content: str = "", embed: discord.Embed = None, ephemeral=False):
        try:
            safe_chunks = self.__split_to_chunks(content=content)
            if interaction:
                for chunk in safe_chunks:
                    if chunk != "":
                        await interaction.followup.send(content=f"```{chunk}```", ephemeral=ephemeral)
                if embed:
                    await interaction.followup.send(embed=embed, ephemeral=ephemeral)
            if user:
                for chunk in safe_chunks:
                    if chunk != "":
                        await user.send(content=f"```{chunk}```")
                if embed:
                    await user.send(embed=embed)
        except Exception as e:
            logger.warning(f"Failure: {e}")

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

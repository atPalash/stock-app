from collections.abc import Callable
from datetime import tzinfo
from importlib import import_module
import inspect
import os
import logging
from typing import Iterable, Iterator
from attr import dataclass
import discord
from discord.ext import commands
from dotenv import load_dotenv
import pandas

from pytick.llm.graph import Graph
from pytick.scheduler.scheduler import Scheduler
from pytick.utility.utility import get_logger

logger = get_logger(__file__, logging.DEBUG)

@dataclass(frozen=True)
class BotConfig:
    """Configuration parameters for the Discord bot during initialisation."""
    command_prefix: str
    token: str
    query_handler: object
    llm_convert_msg: str
    tz: tzinfo
    schedules: dict
    users_config: dict
    update_users_callback: Callable[[str, dict], None]
    zerodha_df: pandas.DataFrame
    trading_view_url: str
    zerodha_url: str
    link_type: str

class DiscordBot:
    """Encapsulates a Discord bot that prefers sending replies as DMs and falls back to channel messages.

    Usage:
        bot = DiscoBot(command_prefix='/', token=os.getenv('DISCORD_BOT_TOKEN'))
        bot.run()
    """

    def __init__(self, config: BotConfig):
        intents = discord.Intents.default()
        intents.message_content = True
        self.bot = commands.Bot(command_prefix=config.command_prefix, intents=intents)
        self.config = config
        self.users_config = config.users_config
        self.llm_handlers = {}
        self.schedulers = {}
        self.__register_commands()

        # register on_ready event (bot.event accepts a coroutine function)
        self.bot.event(self.on_ready)
        # register an error handler to control behavior for missing commands
        self.bot.event(self.on_command_error)

    def get_llm_handler(self, user_id: int) -> Graph:
        if user_id not in self.llm_handlers:
            self.llm_handlers[user_id] = Graph()
        return self.llm_handlers.get(user_id)
    
    def get_scheduler(self, user_id: int) -> Graph:
        if user_id not in self.schedulers:
            self.schedulers[user_id] = Scheduler(self.config.tz, is_async=True)
        return self.schedulers.get(user_id)

    def get_user_config(self, ctx: commands.Context) -> dict:
        user_id = ctx.author.id
        user_name = ctx.author.name
        author = ctx.author.global_name
        if user_id not in self.users_config:
            self.users_config[user_id] = {           
                'user_name': user_name,
                'author': author,
                'subscribed_queries': []
            }
        return self.users_config.get(user_id)
    
    async def on_ready(self):
        logger.info(f'Logged in as {self.bot.user}\nSubscribing to queries')
    
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
            logger.exception(f"Error in command {ctx.command} invoked by {ctx.author}")
            # Optionally notify the user
            try:
                await ctx.send("An internal error occurred while executing the command.")
            except Exception:
                pass
            return

        # Fallback: log unexpected errors
        logger.exception(f"Unhandled command error: {error}")

    def __register_commands(self):
        # Import the module that contains command handlers
        cmd_mod = import_module("pytick.bot.commands")

        # Collect all coroutine functions exported by the module (ignore private names)
        supported_commands = {}
        for name, func in inspect.getmembers(cmd_mod, inspect.iscoroutinefunction):
            if name.startswith("_"):
                continue
            supported_commands[name] = func

        # Register each function as a discord command using its function name
        for name, func in supported_commands.items():
            cmd = commands.Command(func, name=name, help=func.__doc__, extras={'discordbot': self})
            self.bot.add_command(cmd)

    def run(self):
        self.bot.run(self.config.token)

    def update_subscription(self, user_id: int , subscribed_queries: list[dict]):
        self.users_config[user_id]['subscribed_queries'] = subscribed_queries
        self.config.update_users_callback('users', self.users_config)
        
    @staticmethod
    def chunk_lines(parts: Iterable[str], max_len: int = 4096, sep: str = "\n") -> Iterator[str]:
        """
        Yield newline-joined chunks of parts so each chunk's length <= max_len.
        sep controls the join separator (default newline).
        """
        chunk: list[str] = []
        length = 0
        sep_len = len(sep)

        for p in parts:
            # length added if we append p (include separator only if chunk not empty)
            add_len = len(p) if not chunk else sep_len + len(p)
            if length + add_len > max_len:
                if chunk:
                    yield sep.join(chunk)
                chunk = [p]
                length = len(p)
            else:
                chunk.append(p)
                length += add_len

        if chunk:
            yield sep.join(chunk)


if __name__ == '__main__':
    load_dotenv()
    token = os.getenv('DISCORD_BOT_TOKEN')
    DiscordBot(token=token, query_handler=None, llm_convert_msg='').run()

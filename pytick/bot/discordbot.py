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
from pytick.utility.utility import get_logger, read_config

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
    update_users_callback: Callable[[str, dict], None]
    zerodha_df: pandas.DataFrame
    trading_view_url: str
    zerodha_url: str
    link_type: str
    backtest_iterations: int
    default_ticker: str

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
        self.users_config_path = config.users_config_path
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
        user_config_file = f"{self.users_config_path}/{user_id}.yaml"
        user_config = {}
        if not os.path.exists(user_config_file):
            # Create an empty user config file if it doesn't exist
            with open(user_config_file, 'w') as f:
                user_config = {           
                    'user_id': user_id,
                    'user_name': user_name,
                    'author': author,
                    'subscribed_queries': [],
                    'chart': 'tradingview'
                }
            self.config.update_users_callback(user_config_file, user_config, None)
        else: 
            user_config = read_config(user_config_file)  
        return user_config
    
    def update_user_config(self, ctx: commands.Context, user_config: dict):
        user_id = ctx.author.id
        user_config_file = f"{self.users_config_path}/{user_id}.yaml"
        self.config.update_users_callback(user_config_file, user_config, None)
    
    async def on_ready(self):
        logger.info(f'Logged in as {self.bot.user}\nSubscribing to queries')
        # Send hello message to all users on bot alive
        try:
            import yaml
            user_ids = []
            # List all user config files
            users_dir = self.users_config_path
            for fname in os.listdir(users_dir):
                if fname.endswith('.yaml'):
                    with open(os.path.join(users_dir, fname), 'r') as f:
                        data = yaml.safe_load(f)
                        uid = data.get('user_id')
                        if uid:
                            user_ids.append(uid)
            for uid in user_ids:
                user = await self.bot.fetch_user(int(uid))
                try:
                    await user.send('Hello! 👋 The bot is now alive.')
                except Exception as e:
                    logger.warning(f"Could not send hello to user {uid}: {e}")
        except Exception as e:
            logger.warning(f"Error sending hello messages: {e}")
    
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

    def update_subscription(self, ctx: commands.Context , subscribed_queries: list[dict]):
        user_id = ctx.author.id
        user_config_file = f"{self.users_config_path}/{user_id}.yaml"
        
        to_update = read_config(user_config_file)
        # to_update['subscribed_queries'] = subscribed_queries
        self.config.update_users_callback(user_config_file, subscribed_queries,'subscribed_queries')


if __name__ == '__main__':
    load_dotenv()
    token = os.getenv('DISCORD_BOT_TOKEN')
    DiscordBot(token=token, query_handler=None, llm_convert_msg='').run()

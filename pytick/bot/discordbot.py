from importlib import import_module
import inspect
import os
import logging
import discord
from discord.ext import commands
from dotenv import load_dotenv

from pytick.utility.utility import get_logger

logger = get_logger(__file__, logging.DEBUG)

class DiscordBot:
    """Encapsulates a Discord bot that prefers sending replies as DMs and falls back to channel messages.

    Usage:
        bot = DiscoBot(command_prefix='/', token=os.getenv('DISCORD_BOT_TOKEN'))
        bot.run()
    """

    def __init__(self, token: str, command_prefix='/'):
        intents = discord.Intents.default()
        intents.message_content = True
        self.bot = commands.Bot(command_prefix=command_prefix, intents=intents)
        self.token = token 

        self.__register_commands()

        # register on_ready event (bot.event accepts a coroutine function)
        self.bot.event(self.on_ready)
        # register an error handler to control behavior for missing commands
        self.bot.event(self.on_command_error)

    async def on_ready(self):
        print(f'Logged in as {self.bot.user}')
    
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
            cmd = commands.Command(func, name=name, help=func.__doc__)
            self.bot.add_command(cmd)

    def run(self):
        if not self.token:
            raise RuntimeError('Discord bot token not provided (env DISCORD_BOT_TOKEN)')
        self.bot.run(self.token)


if __name__ == '__main__':
    load_dotenv()
    token = os.getenv('DISCORD_BOT_TOKEN')
    DiscordBot(token=token).run()

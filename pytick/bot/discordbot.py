import os
import discord
from discord.ext import commands
from dotenv import load_dotenv


class DiscordBot:
    """Encapsulates a Discord bot that prefers sending replies as DMs and falls back to channel messages.

    Usage:
        bot = DiscoBot(command_prefix='/', token=os.getenv('DISCORD_BOT_TOKEN'))
        bot.run()
    """

    def __init__(self, token: str, command_prefix='/' ):
        intents = discord.Intents.default()
        intents.message_content = True
        self.bot = commands.Bot(command_prefix=command_prefix, intents=intents)
        self.token = token 

        self.__register_commands()
        
    def __register_commands(self):
        async def safe_dm(user, content: str) -> bool:
            """Try to DM `user`. If DMs are blocked, return False. Otherwise return True."""
            try:
                await user.send(content)
                return True
            except discord.Forbidden:
                return False
            except Exception:
                return False

        async def on_ready():
            print(f'Logged in as {self.bot.user}')

        async def ping(ctx: commands.Context):
            sent = await safe_dm(ctx.author, "Pong!")
            if not sent:
                await ctx.send(f"{ctx.author.mention}, I couldn't DM you. Here: Pong!")

        async def helpme(ctx: commands.Context):
            # Build help dynamically from registered commands
            lines = ["**Bot Commands:**"]
            for cmd in self.bot.commands:
                if getattr(cmd, 'hidden', False):
                    continue
                signature = cmd.qualified_name
                brief = cmd.help or cmd.brief or ""
                lines.append(f"`/{signature}` - {brief}")

            help_text = "\n".join(lines)

            sent = await safe_dm(ctx.author, help_text)
            if not sent:
                await ctx.send(f"{ctx.author.mention}, I couldn't DM you. Here are the commands:\n{help_text}")
        
        self.bot.add_command(commands.Command(ping, name='ping'))
        self.bot.add_command(commands.Command(helpme, name='helpme'))

    def run(self):
        if not self.token:
            raise RuntimeError('Discord bot token not provided (env DISCORD_BOT_TOKEN)')
        self.bot.run(self.token)


if __name__ == '__main__':
    load_dotenv()
    token = os.getenv('DISCORD_BOT_TOKEN')
    DiscordBot(token=token).run()

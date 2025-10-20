import discord
from discord.ext import commands

async def __validate(ctx: commands.Context, *args:str): 
    if not args:
        await ctx.send(f"Usage: `/{ctx.invoked_with}` <text>")
        return False
    return True

async def helpme(ctx: commands.Context):
    """Show available bot commands via DM (falls back to channel)."""
    lines = ["**Bot Commands:**"]
    for cmd in ctx.bot.commands:
        if getattr(cmd, "hidden", False):
            continue
        signature = cmd.qualified_name
        brief = cmd.help or cmd.brief or ""
        lines.append(f"`/{signature}` - {brief}")

    help_text = "\n".join(lines)
    try:
        await ctx.author.send(help_text)
    except discord.Forbidden:
        await ctx.send(f"{ctx.author.mention}, I couldn't DM you. Here are the commands:\n{help_text}")
    except Exception:
        await ctx.send("Unable to deliver help right now.")

async def save(ctx: commands.Context):
    """Save the current gherkin query."""
    await ctx.send("(save) functionality not implemented.")

async def convert(ctx: commands.Context, *args: str):
    """Convert the user query to valid gherkin. Usage: `/convert` <text>
    """
    if not await __validate(ctx, *args):
        return
    query = " ".join(args)
    await ctx.send(f"(gherkin) functionality not implemented. Received: {query}")

async def delete(ctx: commands.Context):
    """Delete a gherkin from server."""
    await ctx.send("(delete_gherkin) functionality not implemented.")

async def get(ctx: commands.Context):
    """Get gherkin by id or all stored gherkin query."""
    await ctx.send("(get_gherkin) functionality not implemented.")

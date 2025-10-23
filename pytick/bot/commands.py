import logging
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import pandas

from pytick.llm.graph import Graph
from pytick.utility.utility import get_logger

logger = get_logger(__file__, logging.DEBUG)
load_dotenv()
zerodha_df = pandas.read_csv(os.getenv("ZERODHA_INSTRUMENT_TOKEN_CSV_PATH", ""))
trading_view_url = os.getenv("TRADING_VIEW_URL", "")
zerodha_url = os.getenv("ZERODHA_URL", "")
link_type = os.getenv("LINK_TYPE", "zerodha").lower()

async def __validate(ctx: commands.Context, *args:str) -> tuple[bool, Graph]: 
    llm_handler = ctx.command.extras.get('discordbot').get_llm_handler(ctx.author.id)
    query_handler = ctx.command.extras.get('discordbot').query_handler
    if not llm_handler:
        raise Exception("LLM handler not found.")
    if not args:
        await ctx.send(f"Usage: `/{ctx.invoked_with}` <text>")
        return False, llm_handler
    return True, llm_handler, query_handler

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
    
async def delete(ctx: commands.Context):
    """Delete a gherkin from server."""
    await ctx.send("(delete_gherkin) functionality not implemented.")

async def get(ctx: commands.Context):
    """Get gherkin by id or all stored gherkin query."""
    await ctx.send("(get_gherkin) functionality not implemented.")

async def convert(ctx: commands.Context, *args: str):
    """Convert the user query to valid gherkin. Usage: `/convert` <text>
    """
    valid, llm_handler, _ = await __validate(ctx, *args)
    if not valid:
        return
    try:
        data = f"{llm_handler.run(" ".join(args))}"
        await ctx.send(f"""**Query**\n```{data}```""")
        return data
    except Exception as e:
        await ctx.send(f"Error during conversion: {e}")
        return None

async def run(ctx: commands.Context, *args: str):
    """Convert the query and run to fetch results. Usage: `/run` <text>
    """
    query = await convert(ctx, *args)
    valid, _, query_handler = await __validate(ctx, *args)
    if not valid or not query:
        return
    
    try:
        success, results, errors = query_handler.get_gherkin_result(gherkin_str=query)
        if not success:
            msg = f"Error during query execution: {errors}"
            await ctx.send(msg)
            logger.error(msg)
            return   

        parts = []
        for point in results:
            for qid, tickers in point.items():
                parts.append(f"**{qid}**")
                if link_type == "zerodha":
                    for t in tickers:
                        token = zerodha_df.query(f"tradingsymbol == '{t}' and exchange == 'NSE'")['instrument_token'].iloc[0]
                        parts.append(f"[{t}]({zerodha_url}{t}/{token})")
                    parts.append("")
                else: # link type tradingview
                    parts.append("\n".join(f"[{t}]({trading_view_url}{t})" for t in tickers))
                    parts.append("")

        for i, desc in enumerate(ctx.command.extras.get('discordbot').chunk_lines(parts, max_len=4096)):
            title = "Result" if i == 0 else "Result (cont.)"
            embed = discord.Embed(title=title, description=desc.strip(), color=discord.Color.blurple())
            await ctx.send(embed=embed)
    except Exception as e:
        msg = f"Error during execution: {e}"
        await ctx.send(msg)
        logger.error(msg)
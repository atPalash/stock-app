import logging
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import pandas

from pytick.llm.graph import Graph
from pytick.query.query import QueryHandler
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
    llm_convert_msg = ctx.command.extras.get('discordbot').llm_convert_msg
    if not llm_handler:
        raise Exception("LLM handler not found.")
    if not args:
        await ctx.send(f"Usage: `/{ctx.invoked_with}` <text>")
        return False, llm_handler
    return True, llm_handler, query_handler, llm_convert_msg

async def helpme(ctx: commands.Context, *args: str):
    """Show available bot commands. 
    
    Supported indicators and their configuration are:
        sma:
            periods: [5, 10, 20, 50, 100, 200]
            sources: ["Open", "High", "Low", "Close"]
        ema:
            periods: [5, 10, 20, 50, 100, 200]
            sources: ["Open", "High", "Low", "Close"]
        atr:
            periods: [10, 14]
            sources: ["Close"]
        vwap:
            periods: [10]
            sources: ["Open", "High", "Low", "Close"]
        rvol:
            periods: [10, 20]
            sources: ["Volume"]
    Supported indexes are: nifty50
    
    Usage:
    1. /helpme
    2. /helpme <command>
    """
    lines = []
    
    await ctx.send(f"""**Bot Commands:**""")

    def func(cmd):
        if getattr(cmd, "hidden", False):
            return
        signature = cmd.qualified_name
        brief = cmd.help or cmd.brief or ""
        lines.append(f"```/{signature} - {brief}```")

    if len(args) > 0 and args[0] != "":
        cmd = ctx.bot.get_command(args[0])
        func(cmd)
    else:
        for cmd in ctx.bot.commands:
            func(cmd)

    help_text = "\n".join(lines)
    try:
        await ctx.author.send(help_text)
    except discord.Forbidden:
        await ctx.send(f"{ctx.author.mention}, I couldn't DM you. Here are the commands:\n{help_text}")
    except Exception:
        await ctx.send("Unable to deliver help right now.")

# async def save(ctx: commands.Context):
#     """Save the current gherkin query."""
#     await ctx.send("(save) functionality not implemented.")
    
# async def delete(ctx: commands.Context):
#     """Delete a gherkin from server."""
#     await ctx.send("(delete_gherkin) functionality not implemented.")

# async def get(ctx: commands.Context):
#     """Get gherkin by id or all stored gherkin query."""
#     await ctx.send("(get_gherkin) functionality not implemented.")

async def edit(ctx: commands.Context, *args: str):
    """User tries different queries to convert it to valid gherkin. 

    Usage: 
    1. /edit <text>
    """
    valid, llm_handler, _, llm_convert_msg = await __validate(ctx, *args)
    if not valid:
        await ctx.send(f"""Cannot convert the query to gherkin. Usage: `/convert` <text>""")
        return
    try:
        to_convert = " ".join(args)
        logger.info(f"Converting query to gherkin: {to_convert}")
        await ctx.send(f"""**{llm_convert_msg}**""")
        data = f"{llm_handler.run(to_convert)}"
        await ctx.send(f"""**Query**""")
        await ctx.send(f"""```{data}```""")
        return data
    except Exception as e:
        await ctx.send(f"Error during conversion: {e}")
        return None

async def run(ctx: commands.Context, *args: str):
    """Convert a query to gherkin and execute to fetch result. If replying to a
    message or a already valid gherkin execute

    Usage: 
    1. /run <text>
    2. /run as a reply to a message containing gherkin text.
    3. /run <gherkin text>
    """
    query = pre_check(ctx, *args)
    if query == "":
        query = await edit(ctx, *args)
    else:
        await ctx.send(f"""**Query**""")
        await ctx.send(f"""```{query}```""")
    args = (query,)
    valid, _, query_handler, _ = await __validate(ctx, *args)
    if not valid or not query:
        return
    
    try:
        success, results, errors, _ = query_handler.get_gherkin_result(gherkin_str=query)
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

def pre_check(ctx: commands.Context, *args: str) -> bool:
    """Pre-check to extract gherkin text from reply or arguments.
    """
    gherkin_text = ""
    try:
        replied_text = ctx.message.reference.resolved.content
        if replied_text != "":
            gherkin_text = replied_text.strip('`')
    except Exception:
        try:
            gherkin_text = (' ').join(ctx.message.content.split(' ')[1:]).strip('`')
            is_valid, _, errors = QueryHandler.parse_gherkin(gherkin_text)
            if not is_valid:
                gherkin_text = ""
        except Exception:
            pass
    return gherkin_text
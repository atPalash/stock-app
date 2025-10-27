import logging
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import pandas

from pytick.bot.discordbot import BotConfig
from pytick.llm.graph import Graph
from pytick.query.query import QueryHandler
from pytick.utility.utility import get_logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = get_logger(__file__, logging.DEBUG)
load_dotenv()

async def __validate(ctx: commands.Context, *args:str) -> tuple[bool, Graph]: 
    try:
        llm_handler = ctx.command.extras.get('discordbot').get_llm_handler(ctx.author.id)
        scheduler = ctx.command.extras.get('discordbot').get_scheduler(ctx.author.id)
        user_config = ctx.command.extras.get('discordbot').get_user_config(ctx)
        bot_config = ctx.command.extras.get('discordbot').config
        
        if not args:
            await ctx.send(f"Usage: `/{ctx.invoked_with}` <text>")
            return False, None, None, None, None, None
        return True, bot_config, user_config, llm_handler, scheduler
    except Exception as e:
        msg = f"Error during validation: {e}"
        await ctx.send(msg)
        logger.error(msg)
        return False, None, None, None, None

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

async def edit(ctx: commands.Context, *args: str):
    """User tries different queries to convert it to valid gherkin. 

    Usage: 
    1. /edit <text>
    """
    valid, bot_config, _, llm_handler, _ = await __validate(ctx, *args)
    if not valid:
        await ctx.send(f"""Cannot convert the query to gherkin. Usage: `/convert` <text>""")
        return
    try:
        to_convert = " ".join(args)
        logger.info(f"Converting query to gherkin: {to_convert}")
        await ctx.send(f"""**{bot_config.llm_convert_msg}**""")
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
    query = __pre_check(ctx, *args)
    if query == "":
        query = await edit(ctx, *args)
    else:
        await ctx.send(f"""**Query**""")
        await ctx.send(f"""```{query}```""")
    args = (query,)
    valid, bot_config, user_config, _, _ = await __validate(ctx, *args)
    if not valid or not query:
        return
    
    try:
        _, parts = __do_run(bot_config, query)
        # __update_result(ctx, user_config, query, tickers)
        await __sendEmbedResults(ctx=ctx, parts=parts)
    except Exception as e:
        msg = f"Error during execution: {e}"
        await ctx.send(msg)
        logger.error(msg)

async def __sendEmbedResults(ctx: commands.Context, parts: list[str]):
    try:
        for i, desc in enumerate(ctx.command.extras.get('discordbot').chunk_lines(parts, max_len=4096)):
            title = "Result" if i == 0 else "Result (cont.)"
            embed = discord.Embed(title=title, description=desc.strip(), color=discord.Color.blurple())
            await ctx.send(embed=embed)
    except Exception as e:
        msg = f"Error during execution: {e}"
        await ctx.send(msg)
        logger.error(msg)

async def sub(ctx: commands.Context, *args: str):
    """Subscribe to a query. The subscription can be made witha reply to exiting 
    gherkin query with period. Valid periods are 1m, 5m, 15m, 30m, 1h. 
    
    Usage: 
    1. /sub <period>
    """
    valid, bot_config, user_config, _, scheduler = await __validate(ctx, *args)
    valid_periods = list(bot_config.schedules.keys())
    check_error_msg = f"Usage: `/{ctx.invoked_with}` <period>. Valid period are {', '.join(valid_periods)}"
    if len(args) != 1 or args[0] not in valid_periods:
        await ctx.send(check_error_msg)
        return
    period = args[0]
    
    query = __pre_check(ctx, *args)
    if query == "":
        await ctx.send(check_error_msg)
        return
    else:
        await ctx.send(f"""**Subscribed to Query with period {period}**""")
    if not valid or not query:
        return
    
    subscription_exists = False
    subscribed_queries = user_config.get('subscribed_queries', [])
    for sub in subscribed_queries:
        if sub['query'] == query:
            subscription_exists = True
            if period != sub['period']:
                sub['period'] = period
                sub['tickers'] = []
                ctx.command.extras.get('discordbot').update_subscription(ctx.author.id, subscribed_queries)
                return
    if not subscription_exists:
        subscribed_queries.append({'query': query, 'period': period, 'tickers': []})
        ctx.command.extras.get('discordbot').update_subscription(ctx.author.id, subscribed_queries)

    try:
        job_func = __make_run_job(ctx, user_config, bot_config, query)
        scheduler.start()
        scheduler.add_periodic_job(job_func, params=bot_config.schedules.get(period), job_id=f"sub_job_{period}")
        # scheduler.add_periodic_job(job_func, params={"second": "*/2"}, job_id=f"sub_job_{period}")
    except Exception as e:
        msg = f"Error during subscription: {e}"
        await ctx.send(msg)
        logger.error(msg)

def __do_run(bot_config: BotConfig, query: str):
    try:
        success, results, errors, _ = bot_config.query_handler.get_gherkin_result(gherkin_str=query)
        if not success:
            msg = f"Error during query execution: {errors}"
            logger.error(msg)
            raise Exception(msg)
            
        parts = []
        for point in results:
            for qid, tickers in point.items():
                parts.append(f"**{qid}**")
                if bot_config.link_type == "zerodha":
                    for t in tickers:
                        token = bot_config.zerodha_df.query(f"tradingsymbol == '{t}' and exchange == 'NSE'")['instrument_token'].iloc[0]
                        parts.append(f"[{t}]({bot_config.zerodha_url}{t}/{token})")
                    parts.append("")
                else: # link type tradingview
                    parts.append("\n".join(f"[{t}]({bot_config.trading_view_url}{t})" for t in tickers))
                    parts.append("")
        return tickers, parts    
    except Exception as e:
        msg = f"Error during execution: {e}"
        logger.error(msg)
        raise Exception(msg)
    

def __pre_check(ctx: commands.Context, *args: str) -> bool:
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

def __update_result(ctx, user_config:dict, query:str, tickers:list[str]) -> bool:
    subscribed_queries = user_config.get('subscribed_queries', [])
    to_update = True
    for qry in subscribed_queries:
        if qry['query'] == query:
            last_result = qry.get('tickers', [])
            to_update = False
            if last_result != tickers:
                last_result = tickers
                qry['tickers'] = last_result
                to_update = True
    if to_update:
        ctx.command.extras.get('discordbot').update_subscription(ctx.author.id, subscribed_queries)
    return to_update

def __make_run_job(ctx, user_config:dict, bot_config:BotConfig, query: str):
    async def job():
        tickers, _ = __do_run(bot_config, query)
        if __update_result(ctx, user_config, query, tickers):
            # logger.info(f"Sending subscription result to user {user_config.get('user_name')}")
            await run(ctx, (query,))
        # else:
            # logger.info(f"No change in result for user {user_config.get('user_name')}, not sending update.")
    return job
import logging
import os
from random import randint
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

async def send_long_message(destination, content: str, max_length: int = 1990):
    """Send a message that may exceed Discord's 2000 character limit by splitting it.
    
    Args:
        destination: Can be ctx (Context) for channel, ctx.author (User/Member) for DM, or any messageable
        content: The message content
        max_length: Max chars per message (default 1990)
    """
    # Handle both ctx.send() and user.send()
    send_func = destination.send if hasattr(destination, 'send') else destination.send
    
    if len(content) <= max_length:
        await send_func(content)
        return
    
    # Split into chunks
    chunks = []
    while content:
        if len(content) <= max_length:
            chunks.append(content)
            break
        
        # Find a good split point (newline or space)
        split_at = content.rfind('\n', 0, max_length)
        if split_at == -1:
            split_at = content.rfind(' ', 0, max_length)
        if split_at == -1:
            split_at = max_length
        
        chunks.append(content[:split_at])
        content = content[split_at:].lstrip()
    
    # Send all chunks
    for chunk in chunks:
        await send_func(chunk)

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
        msg = f"Exception during validation: {e}"
        await ctx.send(msg)
        logger.warning(msg)
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
        await send_long_message(ctx.author, help_text)
    except discord.Forbidden:
        await send_long_message(ctx, f"{ctx.author.mention}, I couldn't DM you. Here are the commands:\n{help_text}")
    except Exception as e:
        await ctx.send(f"Unable to deliver help right now: {e}")

async def edit(ctx: commands.Context, *args: str):
    """User tries different queries to convert it to valid gherkin. 

    Usage: 
    1. /edit <text>
    2. /edit as a reply to a message containing gherkin text.
    """
    valid, bot_config, _, llm_handler, _ = await __validate(ctx, *args)
    query = __pre_check(ctx, *args)
    if not valid:
        await ctx.send(f"""Cannot convert the query to gherkin. Usage: `/convert` <text>""")
        return
    try:
        to_convert = " ".join(args)
        to_convert = to_convert + '\n' +  query
        await ctx.send(f"""**{bot_config.llm_convert_msg}**""")
        data = f"{llm_handler.run(to_convert)}"
        await ctx.send(f"""**Query**""")
        await ctx.send(f"""```{data}```""")
        return data
    except Exception as e:
        msg = f"Exception during conversion: {e}"
        logger.warning(msg)
        await ctx.send(msg)
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
    changed = []
    parts = []
    if len(args) == 1:
        data = args[0]
        if len(data) == 1:
            query = data[0]
        elif len(data) == 3:
            query = data[0]
            changed = data[1]
            parts = data[2]
    
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
        if len(parts) == 0:
            _, parts = __do_run(bot_config, user_config, query, changed)
        await __sendEmbedResults(ctx=ctx, parts=parts)
    except Exception as e:
        msg = f"Exception during execution: {e}"
        await ctx.send(msg)
        logger.warning(msg)

async def __sendEmbedResults(ctx: commands.Context, parts: list[str]):
    try:
        embed = discord.Embed(title="Result", color=discord.Color.blurple())
        current_section = ""
        field_count = 0
        
        for part in parts:
            # Handle section headers
            if part.startswith("**") or part.strip() == "":
                if part.strip() != "":
                    current_section = part.replace('*', '')
                    embed.add_field(name=current_section, value="⎯" * 20, inline=False)
                    field_count += 1
                continue
            
            # Add ticker with all its links
            if part.strip():
                # Use zero-width space for empty name to group under section
                embed.add_field(name="​", value=part, inline=False)
                field_count += 1
            
            # Send when embed gets too large (Discord limit is 25 fields)
            if field_count >= 20:
                await ctx.send(embed=embed)
                embed = discord.Embed(title="Result (cont.)", color=discord.Color.blurple())
                if current_section:
                    embed.add_field(name=current_section, value="⎯" * 20, inline=False)
                field_count = 1 if current_section else 0
        
        # Send final embed if it has fields
        if field_count > 0:
            await ctx.send(embed=embed)
    except Exception as e:
        # msg = f"Exception during execution: {e}"
        # await ctx.send(msg)
        logger.warning(e)
        raise e
        
async def sub(ctx: commands.Context, *args: str):
    """Subscribe to a query. The subscription can be made witha reply to exiting 
    gherkin query with period. Valid periods are 1m, 5m, 15m, 30m, 1h. 
    
    Usage: 
    1. /sub <period>
    2. /sub list - to list queries available for subscriptions
    3. /sub remove <query> - to remove a subscription
    """
    valid, bot_config, user_config, _, scheduler = await __validate(ctx, *args)
    valid_periods = list(bot_config.schedules.keys())
    check_error_msg = f"Usage: `/{ctx.invoked_with}` <period>. Valid period are {', '.join(valid_periods)}"
    if len(args) != 1:
        await ctx.send(check_error_msg)
        return
    period = args[0]
    
    query = __pre_check(ctx, *args)

    subscription_exists = False
    subscribed_queries = user_config.get('subscribed_queries', [])
    try:
        if period == 'list':    
            if not subscribed_queries:
                await ctx.send(f"No subscriptions found.")
                return
            await ctx.send("**Subscribed Queries:**")
            for sub in subscribed_queries:
                await ctx.send(f"```{sub['query']}```")
                await ctx.send(f"```{sub['period']}```")
            return
        elif period == 'remove':
            for sub in subscribed_queries:
                if sub['query'] == query:
                    subscribed_queries.remove(sub)
                    ctx.command.extras.get('discordbot').update_subscription(ctx, subscribed_queries)
                    scheduler.remove_job(f"sub_job_{query}")
                    await ctx.send(f"Removed subscription for query.")
                    return
            await ctx.send(f"No subscription found for the given query.")
            return
        elif period in valid_periods:
            if query == "":
                await ctx.send(check_error_msg)
                return
            else:
                await ctx.send(f"""**Subscribed to Query with period {period}**""")
            if not valid or not query:
                return
            for sub in subscribed_queries:
                if sub['query'] == query:
                    subscription_exists = True
                    if period != sub['period']:
                        sub['period'] = period
                        sub['tickers'] = []
                        ctx.command.extras.get('discordbot').update_subscription(ctx, subscribed_queries)
                        return
            if not subscription_exists:
                subscribed_queries.append({'query': query, 'period': period, 'tickers': []})
                ctx.command.extras.get('discordbot').update_subscription(ctx, subscribed_queries)

            try:
                job_func = __make_run_job(ctx, bot_config, query)
                scheduler.start()
                scheduler.add_periodic_job(job_func, params=bot_config.schedules.get(period), job_id=f"sub_job_{query}")
                # scheduler.add_periodic_job(job_func, params={"second": "*/2"}, job_id=f"sub_job_{period}")
            except Exception as e:
                msg = f"Exception during subscription: {e}"
                await ctx.send(msg)
                logger.warning(msg)
        else:
            msg=f"Invalid sub args"
            await ctx.send(msg)
            logger.warning(msg)
    except Exception as e:
        msg = f"Exception during subscription: {e}"
        await ctx.send(msg)
        logger.warning(msg)

async def bt(ctx: commands.Context, *args: str):
    """Backtest a query. The query to include 2 list conditions named bull & bear.
    By default 10 iterations of backtest are run starting from random position with
    lookback from the reference. e.g. if lookback is 10 and interval is 5m, 10 backtests
    are run with 5 minute interval ohlc. Starting from random positions with 10 
    candles back as the starting point to simulate forward testing for next 10 candles. 
    
    Usage: 
    1. /bt <lookback> <interval> - reply to a query with backtest conditions
    <lookback> is integer number. <interval> is one of 1m, 5m, 15m, 30m, 1h, 1d
    """
    valid, bot_config, _, _, _ = await __validate(ctx, *args)
    check_error_msg = f"Usage: `/{ctx.invoked_with}` <lookback> <interval>. lookback is integer number. interval is one of {', '.join(bot_config.schedules.keys())} "
    if len(args) != 2 or not valid:
        await ctx.send(check_error_msg)
        return
    try:
        lookback, interval = args
        lookback = int(lookback)
        interval = str(interval)
        if lookback <= 0:
            raise ValueError("Lookback must be a positive integer.")
        if interval not in bot_config.schedules:
            raise ValueError(f"Invalid interval. Valid intervals are: {', '.join(bot_config.schedules.keys())}")
    except Exception as e:
        await ctx.send(check_error_msg)
        return
    
    query = __pre_check(ctx, *args)
    if query == "":
        await ctx.send(f"Please reply to a gherkin query message to backtest.")
        return
    
    backtests = []
    bk_errors = []
    for i in range(bot_config.backtest_iterations):
        try:
            lookback_i = min(lookback + i * randint(0, i*lookback), 1000)
            success, results, errors, table, datetime = __do_backtest(bot_config, query, 
                                                                      bt_config={
                                                                        'clip': lookback_i, 
                                                                        'forward': lookback, 
                                                                        'interval': interval,
                                                                        'default_ticker': bot_config.default_ticker})
            if not success:
                bk_errors.append(errors)
            backtests.append({'iteration': i, 'lookback': lookback_i, 'positive%': results[0], 
                              'negative%': results[1], 'table': table, 'datetime': datetime})
        except Exception as e:
            bk_errors.append(e)
    if len(bk_errors) > 0:
        await ctx.send(f"Backtest completed with {len(bk_errors)} errors. e.g {bk_errors[0]}")
    
    for bt in backtests:
        await ctx.send(f"**Backtest Iteration {bt['iteration']} on {bt['datetime']}**\nPositive Signals: {bt['positive%']:.2f}%, Negative Signals: {bt['negative%']:.2f}%\nNote: table shows only non-zero score entries.")
        bt_table = bt['table']
        if bt_table is not None and not bt_table.empty:
            bt_table.set_index('ticker', inplace=True)
            bt_table = bt_table.filter(items=['ticker', 'bull', 'bear', 'close_start', 'close_reference', 'score'])
            bt_table = bt_table[bt_table['score'].ne(0)]
            table_str = bt_table.to_markdown()
            await send_long_message(ctx, f"```{table_str}```")

async def config(ctx: commands.Context, *args: str):
    """Do user configuration.
    
    Usage: 
    1. /config show - show current user configuration
    2. /config update <key> <value> - update user configuration key with value.
    Supported keys are config headers in config show.
    """
    valid, _, user_config, _, _ = await __validate(ctx, *args)

    async def send_user_config(config: dict, prefix: str, ctx: commands.Context):
        drop_keys = ['subscribed_queries']
        for key in drop_keys:
            if key in config:
                config.pop(key)
        config_str = pandas.json_normalize(config).to_markdown()
        await send_long_message(ctx, f"{prefix}```{config_str}```")
    
    todo = args[0]
    if not valid:
        return
    try:
        if todo == "show":
            await send_user_config(user_config, "**User Configuration:**\n", ctx)
        elif todo == "update":
            allowed_update_keys = ['chart']
            key = args[1]
            value = args[2]
            if key in user_config and key in allowed_update_keys:
                user_config[key] = value
                ctx.command.extras.get('discordbot').update_user_config(ctx, user_config)
                await send_user_config(user_config, "**User Configuration Updated:**\n", ctx)
            else:
                msg=f"Invalid config key. Allowed keys are {', '.join(allowed_update_keys)}"
                await ctx.send(msg)
                logger.warning(msg)
        else:
            msg=f"Invalid config args"
            await ctx.send(msg)
            logger.warning(msg)
    except Exception as e:
        msg = f"Exception during fetching configuration: {e}"
        await ctx.send(msg)
        logger.warning(msg)

def __do_run(bot_config: BotConfig, user_config: dict, query: str, changed:list=[]) -> tuple[list[dict], list[str]]:
    try:
        success, results, errors, _ = bot_config.query_handler.get_gherkin_result(gherkin_str=query)
        if not success:
            msg = f"Exception during query execution: {errors}"
            logger.warning(msg)
            raise Exception(errors)
            
        parts = []
        for point in results:
            for qid, tickers in point.items():
                parts.append(f"**{qid}**")
                chart_type = user_config.get("chart", "tradingview")
                corporate_actions = bot_config.notification_handler.get_corporate_actions(tickers=tickers)
                for t in tickers:
                    try:
                        chart_link = f"[{t}]({bot_config.trading_view_url}{t})" # default to tradingview chart
                        if chart_type == "zerodha":
                            token = bot_config.zerodha_df.query(f"tradingsymbol == '{t}' and exchange == 'NSE'")['instrument_token'].iloc[0]
                            chart_link = f"[{t}]({bot_config.zerodha_url}{t}/{token})"
                        if chart_type == "tradingview" and any(c in t for c in ['-','&']):
                            edited_t = t.replace('-', '_').replace('&', '_')
                            chart_link = f"[{t}]({bot_config.trading_view_url}{edited_t})"
                        ticker_action = corporate_actions.get(t, None)
                        corporate_action_link = ""
                        if ticker_action is not None and not ticker_action.empty:
                            corporate_action_link = f"[action]({ticker_action['file'].tolist()[0]})"
                        news_link = f"[news](https://www.google.com/finance/quote/{t}:NSE)"
                        changed = "🟢" if t in changed else ""
                        ticker_clickables = [chart_link, news_link, corporate_action_link, changed]
                        parts.append(' '.join(ticker_clickables))
                    except Exception as e:
                        parts.append(f"[{t}]")
                        logger.warning(f"Exception {t}: {e}")
        return results, parts    
    except Exception as e:
        # msg = f"Exception during execution: {e}"
        logger.warning(msg)
        raise e
    
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

def __update_result(ctx, user_config:dict, query:str, tickers:list[dict]) -> tuple[bool, list[dict]]:
    subscribed_queries = user_config.get('subscribed_queries', [])
    to_update = True
    changed = []
    for qry in subscribed_queries:
        if qry['query'] == query:
            last_result = qry.get('tickers', {})
            to_update = False
            if last_result != tickers:
                tickers_changed = []
                for i in range(len(tickers)):
                    id = list(tickers[i].keys())[0]
                    last_tickers = []
                    current_tickers = []
                    try:
                        last_tickers = last_result[i][id]
                        current_tickers = tickers[i][id]
                    except Exception:
                        pass
                    tickers_changed = list(set(current_tickers)-set(last_tickers))
                    changed.append({id: tickers_changed})
                last_result = tickers
                qry['tickers'] = last_result
                to_update = True
               
    if to_update:
        ctx.command.extras.get('discordbot').update_subscription(ctx, subscribed_queries)
                
    return to_update, changed 

def __make_run_job(ctx, bot_config:BotConfig, query: str):
    async def job():
        try:
            user_config = ctx.command.extras.get('discordbot').get_user_config(ctx)
            tickers, parts = __do_run(bot_config, user_config, query)
            to_update, changed = __update_result(ctx, user_config, query, tickers)
            if to_update:
                # logger.info(f"Sending subscription result to user {user_config.get('user_name')}")
                await run(ctx, (query, changed, parts, ))
            # else:
                # logger.info(f"No change in result for user {user_config.get('user_name')}, not sending update.")
        except Exception as e:
            msg = f"Exception during subscription job execution: {e}"
            await ctx.send(msg)
            logger.warning(msg)
    return job

def __do_backtest(bot_config: BotConfig, query: str, bt_config:None) -> tuple[list[dict], list[str]]:
    try:
        success, results, errors, table = bot_config.query_handler.get_gherkin_result(gherkin_str=query, bt_config=bt_config)
        datetime = bot_config.query_handler.get_clip_time(bt_config=bt_config)
        if not success:
            msg = f"Exception during query execution: {errors}"
            logger.warning(msg)
            raise Exception(msg)
        return success, results, errors, table, datetime
    except Exception as e:
        msg = f"Exception during execution: {e}"
        logger.warning(msg)
        raise Exception(msg)
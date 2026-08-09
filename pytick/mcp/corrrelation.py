import logging
import os

from dotenv import load_dotenv
import pandas
from reactivex import interval

from pytick.utility.utility import get_logger, read_config


load_dotenv()
logger = get_logger(__file__, logging.DEBUG)
config = os.environ.get("CONFIG_FILE")
app_config = read_config(file_path=config)


from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio

async def call_save_to_csv(ticker: str, interval: str, columns: list):
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "pytick.mcp.server", "--transport", "stdio"]
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "save_to_csv",
                arguments={"ticker": ticker, "interval": interval, "columns": columns}
            )
            return result.content[0].text if result.content else None
        
def compute(df: pandas.DataFrame) -> pandas.DataFrame:
    df['diff'] = df['close'].diff().round(2)
    df['pct_change'] = df['close'].pct_change().round(2)
    return df

def find_correlation(tickers:list, interval:str):
    if len(tickers) < 2 or any(t not in app_config.get('indexes', {}).get('nifty100', []) for t in tickers) \
    or interval not in app_config.get("cron_schedules", {}).keys():
        logger.error("Invalid tickers provided. Please provide at least two valid tickers from Nifty 100.")
        return

    async def ensure_data(ticker, interval, columns=["close"]):
        await call_save_to_csv(ticker, interval, columns)

    # load csv files for each ticker
    df = pandas.DataFrame()
    for ticker in tickers:
        try:
            # Then in find_correlation or __main__:
            asyncio.run(ensure_data(ticker, interval))    
            ticker_df = pandas.read_csv(f"{ticker}_{interval}.csv")
            ticker_df = compute(ticker_df)
            for col in ticker_df.columns:
                if col != 'datetime':
                    ticker_df.rename(columns={col: f'{ticker}_{col}'}, inplace=True)
            if df.empty:
                df = ticker_df
            else:
                df = pandas.merge(df, ticker_df, on='datetime', how='inner')
        except FileNotFoundError:
            logger.error(f"CSV file for ticker {ticker} not found. Please ensure the CSV files are generated.")
            return

    # Compute correlation per metric (close-close, diff-diff, pct_change-pct_change)
    # df = df.round(2)
    df.to_csv(f"merged_{interval}.csv", index=False)  # Save merged DataFrame for reference
    metrics = ['close', 'diff', 'pct_change']
    for metric in metrics:
        cols = [f"{t}_{metric}" for t in tickers]
        corr = df[cols].corr().round(2)
        corr.to_csv(f"correlation_{metric}.csv")
if __name__ == "__main__":
    find_correlation(tickers=["SBIN", "HDFCBANK", "ICICIBANK", "KOTAKBANK", "AXISBANK", "BANKBARODA", "UNIONBANK"], interval="1d")
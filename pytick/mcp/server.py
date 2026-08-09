import json
import logging
import os
from dotenv import load_dotenv
import httpx
from mcp.server.fastmcp import FastMCP
import pandas
from pydantic import BaseModel, ConfigDict
from typing import Optional
from pytick.utility.utility import get_logger, read_config

# Create an MCP server
mcp = FastMCP("StockApp")

load_dotenv()
logger = get_logger(__file__, logging.DEBUG)
config = os.environ.get("CONFIG_FILE")
app_config = read_config(file_path=config)

def interval_validator(interval: str) -> bool:
    """
    Validate the interval string.
    """
    valid_intervals = app_config.get("cron_schedules", {}).keys()
    return interval in valid_intervals

def ticker_validator(ticker: str) -> bool:
    """
    Validate the stock ticker.
    """
    tickers = list(set(app_config.get('indexes', {}).get('nifty50', []))
                   | set(app_config.get('indexes', {}).get('nifty100', [])))
    return ticker in tickers



class RetVal(BaseModel):
    model_config = ConfigDict(extra='forbid')   # reject unknown keys at runtime
    success: bool
    ticker: str
    error: Optional[str] = None

@mcp.tool()
def save_to_csv(ticker: str, interval: str, columns: list) -> str:
    """
    Get a DataFrame for a stock ticker and interval.
    """
    if not ticker_validator(ticker) or not interval_validator(interval) or len(columns) == 0:
        return RetVal(success=False, ticker=ticker, error='Invalid ticker or interval or empty columns').model_dump_json()

    try:
        resp = httpx.get(f"http://localhost:8000/df/{ticker}/{interval}", timeout=30)
        resp.raise_for_status()
        response_data = json.loads(resp.text)
        data = response_data.get('data', [])

        # Always keep the timestamp column (Datetime) alongside requested columns
        ts_col = 'datetime' if data and 'datetime' in data[0] else None
        final_cols = ([ts_col] if ts_col else []) + [c for c in columns if c != ts_col]
        pandas.DataFrame(data, columns=final_cols).to_csv(f"{ticker}_{interval}.csv", index=False)
        return "saved"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def hello_mcp() -> str:
    """
    Say hello to the MCP server.
    """
    return "Hello from StockApp MCP Server!"

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--transport", default="stdio", choices=["stdio", "sse"])
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    if args.transport == "sse":
        from starlette.middleware.cors import CORSMiddleware
        import uvicorn

        app = mcp.sse_app()
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],      # allow Live Server (5500) and any origin
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    else:
        mcp.run()  # stdio (default for Copilot)

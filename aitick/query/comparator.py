import asyncio
import json
from pydantic import BaseModel
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pytick.query.trade import TradeHandler

import httpx


async def make_post(endpoint: str, data: dict, timeout=1*60*60):
    async with httpx.AsyncClient() as client:
        try:
            # If this task is cancelled (e.g. by the UI), 
            # httpx will drop the connection immediately.
            r = await client.post(
                f"http://localhost:9000/{endpoint}", 
                json=data, 
                timeout=timeout
            )
            return r
        except asyncio.CancelledError:
            print("Request was cancelled by the client-side logic.")
            raise


def plot_strategy_comparison(strategy_data):
    """
    strategy_data: List of dicts, e.g.:
    [
        {"name": "Alpha_Bot", "results": [1.2, -1.0, 5.5, ...]},
        {"name": "Beta_Bot", "results": [-1.0, -1.0, 12.0, ...]}
    ]
    """
    plt.style.use('seaborn-v0_8-muted')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 12))
    
    leaderboard = []

    for strategy in strategy_data:
        name = strategy['query'].strip().split('\n')[1].split(':')[1]
        results = pd.Series(strategy['metrics'])
        # Calculate Cumulative Returns
        cumulative_r = np.cumsum(list(results['r'].values()))
        
        # Calculate Metrics
        expectancy = results['expectancy_r']
        std_dev = results['std_dev_r']
        sqn = results['sqn']
        
        leaderboard.append({
            "Name": name,
            "Expectancy": expectancy,
            "SQN": sqn,
            "Total Trades": len(results)
        })

        # Plot 1: Cumulative Equity Curve
        ax1.plot(cumulative_r, label=f"{name} (SQN: {sqn:.2f})", linewidth=2)

    # Formatting Top Plot
    ax1.set_title("Strategy Comparison: Cumulative R-Return", fontsize=14, fontweight='bold')
    ax1.set_ylabel("Total R-Multiple Earned")
    ax1.set_xlabel("Number of Trades")
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)

    # Plot 2: Distribution Comparison (Violin Plot)
    # This shows the 'density' of wins vs losses
    df_list = []
    for s in strategy_data:
        # 1. Get the cumulative list
        name = s['query'].strip().split('\n')[1].split(':')[1]
        temp_df = pd.DataFrame({'R': list(s['metrics']['r'].values()), 'Strategy': name})
        df_list.append(temp_df)
    
    combined_df = pd.concat(df_list)
    sns.violinplot(data=combined_df, x='Strategy', y='R', ax=ax2, inner="quart")
    
    ax2.set_title("Return Distribution (Risk Profile)", fontsize=14, fontweight='bold')
    ax2.axhline(0, color='black', linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    filename = "strategy_comparison.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    
    # 2. Optional: Close the plot to free up memory
    plt.close()
    
    print(f"\n[Success] Comparison chart saved as: {filename}")

    # Print a text-based leaderboard
    # print("\n--- Strategy Leaderboard ---")
    # print(pd.DataFrame(leaderboard).sort_values(by="SQN", ascending=False).to_string(index=False))
    
class Config(BaseModel):
    queries:list[str]
    start: int
    stop: int
    
class Comparator:
    def __init__(self, config):
        self.config = config
        self.result = {} 
    
    async def compare(self):
        ret = []
        for query in self.config.queries:
            payload = {
                'gherkin': query,
                'start': self.config.start,
                'stop': self.config.stop,
            }
            # Assuming make_post is defined elsewhere in your script
            result = await make_post('backtest', payload, 5*60*60)
            result = json.loads(result.text)
            ret.append({'query': query, 'metrics': result['metrics'] if result else None})
        return ret  

async def main(queries: list[str], start:int, stop:int):
    config = Config(queries=queries, start=start, stop=stop)
    
    comparator = Comparator(config=config)
    
    # 4. Await the async method
    results = await comparator.compare()
    # print(results)
    plot_strategy_comparison(results)

if __name__ == "__main__":
    queries = [
# """
# Feature: pytick llm
# Scenario: Minervini Trend Momentum with Buy and Sell Signals
# Given stocks from index nifty50
# When let close = latest in 1 samples of day close
# And let sma50 = latest in 1 samples of day close sma 50
# And let sma150 = latest in 1 samples of day close sma 100
# And let sma200 = latest in 1 samples of day close sma 200
# Then let buy = (close > sma50) & (sma50 > sma150) & (sma150 > sma200)
# And let sell = (close < sma50)
# """, 
"""
Feature: pytick llm
Scenario: EMA10 and EMA20 rate analysis over 10 samples with close proximity and 0.5*ATR10
Given stocks from index nifty50
When let ema10 = latest in 1 samples of day close ema 10
And let ema20 = latest in 1 samples of day close ema 20
And let ema10_rate = rate in 10 samples of day close ema 10
And let ema20_rate = rate in 10 samples of day close ema 20
And let close = latest in 1 samples of day close
And let atr10 = latest in 1 samples of day close atr 10
Then list buy = tickers with (ema10_rate > 0) & (ema20_rate > 0) & (abs(close - ema20) < atr10)
And list sell = tickers with (ema10_rate < 0) & (ema20_rate < 0) & (abs(close - ema20) < atr10)
""",
"""
Feature: pytick llm
Scenario: Qullamagie parabolic short setup analysis
Given stocks from index nifty50
When let close = latest in 1 samples of day close
And let sma10 = latest in 1 samples of day close sma 10
And let sma20 = latest in 1 samples of day close sma 20
And let atr14 = latest in 1 samples of day close atr 14
And let prev_close = oldest in 2 samples of day close
Then let extension = (close -sma20) / atr14
And list buy = tickers with (extension < -3) & (close > prev_close) & (sma10 < sma20)
And list sell = tickers with (extension > 3) & (close < prev_close) & (sma10 > sma20)
"""
]
    asyncio.run(main(queries=queries, start=500, stop=1))
    
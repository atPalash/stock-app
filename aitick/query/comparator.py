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
        payload = {
            'queries': self.config.queries,
            'start': self.config.start,
            'stop': self.config.stop,
        }
        # Assuming make_post is defined elsewhere in your script
        result = await make_post('backtest', payload, 5*60*60)
        result = json.loads(result.text)
        for pt in result['data']['results']:
            ret.append({'query': pt['query'], 'metrics': pt['metrics']})
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
"""
Feature: pytick llm
Scenario: KQ parabolic short setup analysis
Given stocks from index nifty50
When let close = latest in 1 samples of day close
And let sma10 = latest in 1 samples of day close sma 10
And let sma20 = latest in 1 samples of day close sma 20
And let atr14 = latest in 1 samples of day close atr 14
And let prev_close = oldest in 2 samples of day close
Then let extension = (close -sma20) / atr14
And list sell = tickers with (extension > 3) & (close < prev_close) & (sma10 > sma20)
""", 
"""
Feature: pytick llm
Scenario: KQ Trend following breakout with moving average support using price change
Given stocks from index nifty50
When let close = latest in 1 samples of day close
And let prev_close = oldest in 2 samples of day close
And let ema10 = latest in 1 samples of day close ema 10
And let ema20 = latest in 1 samples of day close ema 20
And let ema50 = latest in 1 samples of day close ema 50
And let mth_change = change in 20 samples of day close
And let three_mth_change = change in 60 samples of day close
And let six_mth_change = change in 120 samples of day close
Then list buy = tickers with (close > ema10) & (ema10 > ema20) & (ema20 > ema50) & (close > prev_close) & ((mth_change > 0.2)| (three_mth_change > 0.5) | (six_mth_change > 0.8))
""",
]
    asyncio.run(main(queries=queries, start=1000, stop=1))
    
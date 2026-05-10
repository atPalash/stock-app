import asyncio
import json
from pydantic import BaseModel
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import io

from pytick.utility.utility import request_server

def plot_strategy_comparison(strategy_data):
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
    # filename = "strategy_comparison.png"
    # plt.savefig(filename, dpi=300, bbox_inches='tight')
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)
    # 2. Optional: Close the plot to free up memory
    plt.close()
    return buffer
    
class Config(BaseModel):
    queries:list[str]
    start: int
    stop: int
    commission: float = 0.01
    
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
            'commission': self.config.commission
        }
        # Assuming request_server is defined elsewhere in your script
        result = await request_server('backtest', payload, 5*60*60)
        result = json.loads(result.text)
        data = []
        for pt in result['data']['results']:
            data.append({'query': pt['query'], 'metrics': pt['metrics'], 'trades': pt['trades']})
            # df = pd.DataFrame(pt['trades'])
            # df.to_csv(f"{pt['query'].strip().splitlines()[1].split(':')[1]} trades.csv", index=False)
        img_buffer = plot_strategy_comparison(data)
        return {'data': data, 'image': img_buffer}

async def run(queries: list[str], start:int, stop:int, commission: float=0.01) -> dict:
    config = Config(queries=queries, start=start, stop=stop, commission=commission)
    comparator = Comparator(config=config)
    results = await comparator.compare()
    return results

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
Then list buy = tickers with (close > ema10) & (ema10 > ema20) & (ema20 > ema50) & (close > prev_close) & ((mth_change > 0.3)| (three_mth_change > 0.5) | (six_mth_change > 0.7))
""",
]
    asyncio.run(run(queries=queries, start=10, stop=1, commission=0.01))
    
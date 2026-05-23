import asyncio
from collections.abc import Callable
import copy
import json
from fastapi import Request
from pydantic import BaseModel
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import io

from pytick.query.query import QueryHandler
from pytick.query.trade import TradeHandler

class Config(BaseModel):
    queries:list[str]
    start: int = 10
    stop: int = 0
    stop_loss: float = 1
    commission: float = 0.01
    
class Comparator:
    def __init__(self, config: Config, disconnected: Callable[[], bool], query_handler:QueryHandler):
        self.disconnected = disconnected
        self.config = config
        self.result = {} 
        self.query_handler = query_handler
    
    async def compare(self) -> dict:
        trades, errors = await self.__do_comparison(self.disconnected, self.query_handler, self.config.queries, self.config.start, self.config.stop, self.config.stop_loss, self.config.commission) 
        data = []
        for pt in trades:
            data.append({'query': pt['query'], 'metrics': pt['metrics'], 'trades': pt['trades'], 'open_trades': pt['open_trades']})
        img_buffer = self.__do_plot(data)
        return {'data': data, 'image': img_buffer}
    
    async def __do_comparison(self, disconnected: Callable[[], bool], query_handler, queries, start, stop, stop_loss, commision) -> list[dict]:
        trade_handlers = [TradeHandler() for _ in queries]
        errors = []
        
        for itr in range(start, stop - 1, -1):
            # 1. Check if the client cancelled the request
            if await disconnected():
                errors.append("Disconnected by client during processing.")
                return [], errors
            
            try:
                # Use asyncio.to_thread() to run CPU-intensive backtest in thread pool
                # This allows the event loop to stay responsive and process other requests
                for i in range(len(queries)):
                    bt_query_handler = copy.deepcopy(query_handler)
                    await asyncio.to_thread(
                        bt_query_handler.get_backtest_result,
                        queries[i],
                        trade_handlers[i],
                        itr,
                        stop_loss
                    )
                    # Yield control to the event loop between queries
                    await asyncio.sleep(0)
            except Exception as e:
                errors.append(str(e))
        
        results = []
        for i in range(len(queries)):
            query = queries[i]
            trade_handler = trade_handlers[i]
            r_multiples = trade_handler.close_df['rmulti'] - commision
            
            # 2. Calculate Fitness Metrics for the AI Agent
            metrics = {
                "total_trades": len(r_multiples),
                "r": r_multiples,
                "expectancy_r": r_multiples.mean() if not r_multiples.empty else 0,
                "std_dev_r": r_multiples.std() if not r_multiples.empty else 0,
                "max_r": r_multiples.max() if not r_multiples.empty else 0,
                "min_r": r_multiples.min() if not r_multiples.empty else 0,
                "win_rate": (r_multiples > 0).sum() / len(r_multiples) if len(r_multiples) > 0 else 0
            }
            # SQN > 1.6: Average, 2.0: Good, 3.0: Excellent, 5.0+: Holy Grail
            metrics["sqn"] = (np.sqrt(metrics["total_trades"]) * 
                    (metrics["expectancy_r"] / (metrics["std_dev_r"] + 1e-6)))
            metrics = {k: round(v, 2) if isinstance(v, (int, float, np.number)) else v for k, v in metrics.items()}
            results.append({
                "query": query, "metrics": metrics, "trades": trade_handler.close_df.to_dict(orient='records'),
                "open_trades": trade_handler.open_df.to_dict(orient='records')
            })
        return results, errors


    def __do_plot(self, strategy_data):
        plt.style.use('seaborn-v0_8-muted')
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 12))

        strategy_names = [s['query'].strip().split('\n')[1].split(':')[1] for s in strategy_data]
    
        # Create a color palette and map it to strategy names
        # This ensures "Strategy A" is the same color in both ax1 and ax2
        colors = sns.color_palette("Set2", len(strategy_names))
        # color_map = dict(zip(strategy_names, colors))
        
        for strategy in strategy_data:
            index = strategy_data.index(strategy)
            name = strategy_names[index]
            results = pd.Series(strategy['metrics'])
            # Calculate Cumulative Returns
            cumulative_r = np.cumsum(list(results['r']))
            
            # Calculate Metrics
            expectancy = results['expectancy_r']
            std_dev = results['std_dev_r']
            sqn = results['sqn']
            
            # Plot 1: Cumulative Equity Curve
            ax1.plot(cumulative_r, label=f"{name}", linewidth=2, color=colors[index])

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
            name = strategy_names[strategy_data.index(s)]
            temp_df = pd.DataFrame({'R': list(s['metrics']['r']), 'Strategy': name})
            df_list.append(temp_df)
        
        combined_df = pd.concat(df_list)

        sns.boxplot(data=combined_df, x='Strategy', y='R', ax=ax2, showfliers=False, palette=colors, hue='Strategy', legend=False)
        sns.stripplot(data=combined_df, x='Strategy', y='R', ax=ax2, alpha=0.5, palette=colors, hue='Strategy', legend=False)
        
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


async def run(disconnected: Callable[[], bool], query_handler: QueryHandler, **kwargs) -> dict:
    config = Config(**kwargs)
    if len(config.queries) == 0 or config.stop < 0:
        raise ValueError(f"Check comparison parameters {config}")
    comparator = Comparator(config=config, disconnected=disconnected, query_handler=query_handler)
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
    
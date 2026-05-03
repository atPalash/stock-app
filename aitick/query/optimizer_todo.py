import asyncio
import logging
import os
from dotenv import load_dotenv
import numpy as np
import ollama
import json
import httpx
import asyncio
from pytick.llm.gherkin_agents.converter import converter_agent as gherkin_converter
from pytick.llm.gherkin_agents.validator import validator_agent as gherkin_validator
from pytick.llm.gherkin_agents.router import router as gherkin_router
from pydantic import BaseModel

from pytick.llm.graph import Graph
from pytick.utility.utility import get_logger, read_config, read_file
logger = get_logger(__file__, logging.DEBUG)
load_dotenv()

# --- Config ---
GENERATIONS = 15
TRAIN_WINDOW = {"start": 100, "stop": 30} # 700 ticks to learn
VAL_WINDOW = {"start": 30, "stop": 0}      # 300 ticks to prove it works

async def make_post(endpoint: str, data:dict):
    async with httpx.AsyncClient() as client:
        r = await client.post(f"http://localhost:9000/{endpoint}", json=data, timeout=5*60*60)
        return r

class QueryConfig(BaseModel):
    llm_prompt: str
    retry_prompt: str
    ollama_model: str
     
class QueryOptimizer():
    def __init__(self, config: QueryConfig):
        self.config = config
        self.champion_query = None
        self.best_robust_score = -float('inf')
        self.history = []

    def calculate_sqn(self, metrics):
        n = metrics.get("total_trades", 0)
        if n < 8: return -2.0 # Higher threshold for robustness
        exp = metrics.get("expectancy_r", 0)
        std = metrics.get("std_dev_r", 0)
        return (exp / (std + 1e-6)) * np.sqrt(n)

    async def run_backtest(self, query, start, stop):
        payload = {
            'gherkin': query,
            'start': start,
            'stop': stop,
        }
        # Assuming make_post is defined elsewhere in your script
        result = await make_post('backtest', payload)
        result = json.loads(result.text)
        return result['metrics'] if result else None

    async def get_mutation(self, query, train_m, val_m, errors=[], retry_count=0):
        """Mutation logic focusing on the GAP between training and validation."""
        prompt = f"""
        Role: Hedge Fund Quant.
        Current Strategy: {query}
        
        PERFORMANCE:
        - Training (In-Sample): Expectancy {train_m['expectancy_r']:.2f}R, SQN {train_m['sqn']:.2f}
        - Validation (Out-of-Sample): Expectancy {val_m['expectancy_r']:.2f}R, SQN {val_m['sqn']:.2f}
        
        CRITIQUE: 
        {"The strategy is ROBUST." if val_m['expectancy_r'] > 0 else "The strategy is OVERFITTED (failed on unseen data). "
        "Ignore the strategy" if val_m['total_trades'] < 5 else "The strategy is valid. Create separate key if required,"
        "Then step should have only one buy and sell for listing the tickers"}
        
        TASK:
        Evolve the Gherkin logic to maximize the Validation Expectancy. 
        If the strategy overfitted, simplify the logic or add a regime filter.
        Return ONLY the updated Gherkin text.
        """
        response = ollama.chat(model=self.config.ollama_model, messages=[{'role': 'user', 'content': prompt}])
        mutated_query = response['message']['content'].strip().replace("```gherkin", "").replace("```", "")
        llm_graph = Graph(
            system_prompt=self.config.llm_prompt,
            retry_prompt=self.config.retry_prompt,
            converter_agent=gherkin_converter,
            validator_agent=gherkin_validator,
            router_agent=gherkin_router,
            ollama_model=self.config.ollama_model)
        converted_query = llm_graph.run(mutated_query, errors=errors, retry_count=retry_count)
        if "Max retries" in converted_query:
            logger
            return query
        return converted_query

    async def optimize(self, initial_query):
        current_query = initial_query
        errors = []
        retry_count = 0
        for gen in range(GENERATIONS):
            print(f"\n--- Generation {gen} ---")
            try:
                # 1. Run Train and Val backtests
                train_metrics = await self.run_backtest(current_query, **TRAIN_WINDOW)
                val_metrics = await self.run_backtest(current_query, **VAL_WINDOW)
                
                if not train_metrics or not val_metrics: continue

                train_sqn = train_metrics['sqn']
                val_sqn = val_metrics['sqn']

                # 2. Fitness = Robustness (Penalty if they diverge)
                # We use the minimum SQN to ensure the agent doesn't ignore the validation set
                robust_score = min(train_sqn, val_sqn)
                
                print(f"Train SQN: {train_sqn:.2f} | Val SQN: {val_sqn:.2f}")
                print(f"Robustness Score: {robust_score:.2f}")

                # 3. Save the Global Champion
                if robust_score > self.best_robust_score:
                    self.best_robust_score = robust_score
                    self.champion_query = current_query
                    print("🏆 NEW GLOBAL CHAMPION (Robust Logic Found)")

                # 4. Mutate
                current_query = await self.get_mutation(current_query, train_metrics, val_metrics)
            except Exception as e:
                errors = e.args[0]
                retry_count = 1
                current_query = await self.get_mutation(current_query, train_metrics, val_metrics, errors, retry_count)
            
        print("\n" + "!"*40)
        print("OPTIMIZATION COMPLETE")
        print(f"Final Robustness Score: {self.best_robust_score:.2f}")
        print(f"Best Gherkin Query:\n{self.champion_query}")
        return self.champion_query

# Execution
if __name__ == "__main__":
    query = """
Feature: pytick llm
Scenario: Qullamagie parabolic short setup analysis
Given stocks from index nifty50
When let close = latest in 1 samples of day close
And let sma10 = latest in 1 samples of day close sma 10
And let sma20 = latest in 1 samples of day close sma 20
And let atr14 = latest in 1 samples of day close atr 14
And let prev_close = oldest in 2 samples of day close
Then let extension = (close -sma20) / atr14
And list sell = tickers with (extension > 3) & (close < prev_close) & (sma10 > sma20)
"""
    app_config = read_config(file_path=os.environ.get("CONFIG_FILE"))
    config = QueryConfig(llm_prompt=read_file(file_path=os.path.join(app_config.get(
        'app_data_path', ''), "llm_prompt_init.prompt.md")), 
        retry_prompt=read_file(file_path=os.path.join(app_config.get(
        'app_data_path', ''), "llm_prompt_retry.prompt.md")), ollama_model='gemma3')
    agent = QueryOptimizer(config=config)
    asyncio.run(agent.optimize(query))

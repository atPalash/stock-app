
import os
import time

import pytest
from dotenv import load_dotenv

from pytick.llm.graph import Graph
from pytick.utility.utility import read_config, read_file


load_dotenv()
config = os.environ.get("CONFIG_FILE")
app_config = read_config(file_path=config)
prompt = read_file(file_path=os.path.join(app_config.get(
    'app_data_path', ''), "llm_prompt_init.prompt.md"))
retry_prompt = read_file(file_path=os.path.join(app_config.get(
    'app_data_path', ''), "llm_prompt_retry.prompt.md"))


OLLAMA_MODELS = ['llama3', 'gemma3']

TEST_QUERIES = [
    {
        'query': 'day close > 1000',
        'check': ['Feature: pytick llm', 'Given stocks from index nifty50', 'close > 1000'],
    },
    {
        'query': '5 minute close > ema10 and close > ema100',
        'check': ['minute5', 'close', 'ema 10', 'ema 100', '&'],
    },
    {
        'query': 'abs(prev_close - close) / prev_close > 0.01 and abs(vwap10 - close) / vwap10 > 0.0',
        'check': ['abs', 'prev_close', 'vwap 10', '&'],
    },
    {
        'query': 'close > previous close',
        'check': ['prev_close', 'oldest in', 'close > prev_close'],
    },
    {
        'query': 'sma20 < open',
        'check': ['sma 20', 'day open', 'sma20 < open'],
    },
    {
        'query': 'ema10 > close',
        'check': ['ema 10', 'day close', 'ema10 > close'],
    },
]


def _assert_gherkin(item, llm_gherkin):
    for core_part in ['Feature: pytick llm', 'Scenario:', 'Given ', 'When ', 'Then ']:
        assert core_part in llm_gherkin

    for key in item['check']:
        assert key in llm_gherkin


@pytest.mark.parametrize('model', OLLAMA_MODELS)
@pytest.mark.parametrize('item', TEST_QUERIES)
def test_model_conversion(model, item):
    handler = Graph(
        system_prompt=prompt,
        retry_prompt=retry_prompt,
        ollama_model=model,
    )
    llm_gherkin = handler.run(user_input=item['query'])
    _assert_gherkin(item, llm_gherkin)


def test_model_conversion_comparative():
    model_results = {}
    total_failures = 0

    for model in OLLAMA_MODELS:
        handler = Graph(
            system_prompt=prompt,
            retry_prompt=retry_prompt,
            ollama_model=model,
        )
        failures = 0
        durations = []
        failed_cases = []

        for item in TEST_QUERIES:
            start = time.perf_counter()
            llm_gherkin = ""
            case_errors = []

            try:
                llm_gherkin = handler.run(user_input=item['query'])
            except Exception as exc:
                case_errors.append(f"runtime error: {exc}")

            duration = time.perf_counter() - start
            durations.append(duration)

            if llm_gherkin:
                for core_part in ['Feature: pytick llm', 'Scenario:', 'Given ', 'When ', 'Then ']:
                    if core_part not in llm_gherkin:
                        case_errors.append(f"missing core part: {core_part}")

                for key in item['check']:
                    if key not in llm_gherkin:
                        case_errors.append(f"missing check token: {key}")

            if case_errors:
                failures += 1
                failed_cases.append({
                    'query': item['query'],
                    'duration': duration,
                    'errors': case_errors,
                })

        avg_duration = sum(durations) / len(durations)
        model_results[model] = {
            'total_cases': len(TEST_QUERIES),
            'failures': failures,
            'passed': len(TEST_QUERIES) - failures,
            'total_time': sum(durations),
            'avg_time': avg_duration,
            'failed_cases': failed_cases,
        }
        total_failures += failures

    lines = ["LLM conversion comparative summary:"]
    for model in OLLAMA_MODELS:
        result = model_results[model]
        lines.append(
            f"- {model}: passed={result['passed']}/{result['total_cases']}, "
            f"failures={result['failures']}, total_time={result['total_time']:.2f}s, "
            f"avg_time={result['avg_time']:.2f}s"
        )
        for case in result['failed_cases']:
            lines.append(
                f"  query='{case['query']}' ({case['duration']:.2f}s): "
                + "; ".join(case['errors'])
            )

    print("\n" + "\n".join(lines))

    if total_failures:
        pytest.fail(
            "Comparative run completed with failures. "
            "See summary above for per-model failure counts and timings."
        )


if __name__ == "__main__":
    test_model_conversion_comparative()

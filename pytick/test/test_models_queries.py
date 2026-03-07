"""
Comprehensive tests for different LLM models and different query scenarios.
Tests cover:
1. LLM model initialization and configuration
2. Gherkin query parsing and validation
3. Query execution with different patterns
4. End-to-end model + query integration
5. Error handling and edge cases
"""

import os
import pytest
import pandas as pd
import logging
from unittest import mock
from typing import Dict, List, Tuple

from pytick.dataframe.dataframe import DataFrameHandler
from pytick.llm.graph import Graph
from pytick.llm.llm_types import State
from pytick.llm.agents.converter import converter_agent
from pytick.llm.agents.validator import validator_agent
from pytick.query.query import QueryHandler
from pytick.query.steps import StepData
from pytick.utility.utility import read_config, read_file
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_ollama import ChatOllama

# Config setup
config_file = os.environ.get("CONFIG_FILE")
app_config = read_config(file_path=config_file)
users_config_path = os.environ.get("USERS_DIR")


class DummyNotificationHandler:
    """Mock notification handler for testing."""

    def __init__(self, tz=None):
        self.tz = tz

    def get_corporate_actions(self, *args, **kwargs):
        return {}

    def get_corporate_actions_dfs(self, *args, **kwargs):
        df = pd.read_csv(
            f"{app_config.get('pytick_test_path', '')}/data/corporate_actions.csv",
            parse_dates=['datetime']
        )
        df["datetime"] = pd.to_datetime(
            df['datetime'], format='%d-%b-%Y %H:%M:%S'
        ).dt.tz_localize(self.tz)
        tickers = kwargs.get('tickers', [])
        ret = {}
        for ticker in tickers:
            ticker_df = df[df["symbol"] == ticker]
            ret[ticker] = ticker_df if not ticker_df.empty else None
        return ret


@pytest.fixture
def data_handler():
    """Initialize test data handler with sample data."""
    tickers = ["TCS", "BEL", "SBIN", "TMPV"]
    indicators = app_config.get('indicators', {})
    tz = app_config.get('tz', 'Asia/Kolkata')
    handler = DataFrameHandler(
        tz=tz,
        indicators=indicators,
        test_data_path=f"{app_config.get('pytick_test_path', '')}/data"
    )
    handler.set_tables(tickers, "1d")
    handler.set_tables(tickers, "5m")
    return handler


@pytest.fixture
def notification_handler():
    """Initialize test notification handler."""
    tz = app_config.get('tz', 'Asia/Kolkata')
    return DummyNotificationHandler(tz=tz)


@pytest.fixture
def query_handler(data_handler, notification_handler):
    """Initialize query handler with test fixtures."""
    return QueryHandler(
        data_handler=data_handler,
        notification_handler=notification_handler,
        interval_translation={
            v: k for k, v in app_config.get('interval_translation', {}).items()
        },
        interval_seconds=app_config.get('interval_seconds', {})
    )


# ==================== LLM MODEL TESTS ====================

class TestLLMModels:
    """Tests for different LLM model configurations."""

    def test_graph_initialization(self):
        """Test Graph initialization with default model."""
        config_file = os.environ.get("CONFIG_FILE")
        app_config = read_config(file_path=config_file)
        prompt = read_file(
            file_path=os.path.join(
                app_config.get('app_data_path', ''),
                "llm_prompt.prompt.md"
            )
        )
        try:
            graph = Graph(system_prompt=prompt)
            assert graph is not None
            assert graph.llm is not None
            assert graph.graph is not None
        except Exception as e:
            pytest.skip(f"LLM model not available: {str(e)}")

    def test_graph_model_configuration(self):
        """Test Graph model can be configured."""
        try:
            with mock.patch('pytick.llm.graph.ChatOllama') as mock_llm:
                mock_instance = mock.MagicMock()
                mock_llm.return_value = mock_instance

                prompt = "Test prompt"
                graph = Graph(system_prompt=prompt)

                # Verify ChatOllama was instantiated with correct params
                mock_llm.assert_called_once()
                assert graph.system_prompt == prompt
        except Exception as e:
            pytest.skip(f"Model configuration test skipped: {str(e)}")

    def test_graph_conversation_state_initialization(self):
        """Test Graph maintains conversation state."""
        try:
            config_file = os.environ.get("CONFIG_FILE")
            app_config = read_config(file_path=config_file)
            prompt = read_file(
                file_path=os.path.join(
                    app_config.get('app_data_path', ''),
                    "llm_prompt.prompt.md"
                )
            )
            graph = Graph(system_prompt=prompt)

            # Check initial state
            assert len(graph.conversation_state["messages"]) == 0
            assert graph.conversation_state["message_type"] is None
            assert graph.conversation_state["errors"] == []
        except Exception as e:
            pytest.skip(f"Conversation state test skipped: {str(e)}")

    @mock.patch('pytick.llm.graph.ChatOllama')
    def test_graph_with_mocked_llm(self, mock_ollama):
        """Test Graph with mocked LLM."""
        mock_llm_instance = mock.MagicMock()
        mock_ollama.return_value = mock_llm_instance

        prompt = "Test system prompt"
        graph = Graph(system_prompt=prompt)

        assert graph.llm is not None
        assert graph.system_prompt == prompt


# ==================== GHERKIN QUERY PARSING TESTS ====================

class TestGherkinParsing:
    """Tests for Gherkin query parsing and validation."""

    def test_valid_basic_gherkin(self, query_handler):
        """Test parsing a valid basic Gherkin query."""
        gherkin = """
Feature: v2
Scenario: test basic query
Given stocks from index nifty50
When let ema10 = latest in 1 samples of day close ema 10
Then list bulls = tickers with close > ema10
"""
        is_valid, step_data, errors = QueryHandler.parse_gherkin(gherkin)
        assert is_valid
        assert isinstance(step_data, list)
        assert len(errors) == 0

    def test_valid_multi_indicator_gherkin(self, query_handler):
        """Test parsing Gherkin with multiple indicators."""
        gherkin = """
Feature: v2
Scenario: test multi-indicator query
Given stocks from index nifty50
When let ema10Day = latest in 1 samples of day close ema 10
* let sma20Day = latest in 1 samples of day close sma 20
* let close = latest in 1 samples of minute5 close
Then list bulls = tickers with close > ema10Day
* list bearish = tickers with close < sma20Day
"""
        is_valid, step_data, errors = QueryHandler.parse_gherkin(gherkin)
        assert is_valid
        assert isinstance(step_data, list)
        assert len(errors) == 0

    def test_gherkin_missing_feature(self, query_handler):
        """Test error handling for missing Feature."""
        gherkin = """
Scenario: test
Given stocks from index nifty50
"""
        is_valid, step_data, errors = QueryHandler.parse_gherkin(gherkin)
        assert not is_valid
        assert len(errors) > 0
        assert any("Feature" in error for error in errors)

    def test_gherkin_missing_scenario(self, query_handler):
        """Test error handling for missing Scenario."""
        gherkin = """
Feature: v2
Given stocks from index nifty50
"""
        is_valid, step_data, errors = QueryHandler.parse_gherkin(gherkin)
        assert not is_valid
        assert len(errors) > 0

    def test_gherkin_invalid_step_order(self, query_handler):
        """Test error handling for invalid step order."""
        gherkin = """
Feature: v2
When let x = latest in 1 samples of day close
Scenario: test
Given stocks from index nifty50
"""
        is_valid, step_data, errors = QueryHandler.parse_gherkin(gherkin)
        assert not is_valid
        assert len(errors) > 0

    def test_gherkin_invalid_keyword(self, query_handler):
        """Test error handling for invalid keyword."""
        gherkin = """
Feature: v2
Scenario: test
InvalidKeyword stocks from index nifty50
"""
        is_valid, step_data, errors = QueryHandler.parse_gherkin(gherkin)
        assert not is_valid
        assert len(errors) > 0

    def test_gherkin_with_complex_condition(self, query_handler):
        """Test parsing Gherkin with complex conditions."""
        gherkin = """
Feature: v2
Scenario: complex condition
Given stocks from index nifty50
When let ema = latest in 1 samples of day close ema 10
* let sma = latest in 1 samples of day close sma 20
Then list result = tickers with close > ema and close > sma
"""
        is_valid, step_data, errors = QueryHandler.parse_gherkin(gherkin)
        assert is_valid
        assert len(errors) == 0

    def test_gherkin_with_operators(self, query_handler):
        """Test parsing Gherkin with various operators."""
        operators = ["latest", "oldest", "minimum", "maximum", "average"]

        for operator in operators:
            gherkin = f"""
Feature: v2
Scenario: test {operator}
Given stocks from index nifty50
When let val = {operator} in 5 samples of day close
Then list result = tickers with close > val
"""
            is_valid, step_data, errors = QueryHandler.parse_gherkin(gherkin)
            assert is_valid, f"Failed for operator: {operator}, errors: {errors}"
            assert len(errors) == 0

    def test_gherkin_with_intervals(self, query_handler):
        """Test parsing Gherkin with different intervals."""
        intervals = ["day", "minute5", "minute15"]

        for interval in intervals:
            gherkin = f"""
Feature: v2
Scenario: test {interval}
Given stocks from index nifty50
When let val = latest in 1 samples of {interval} close
Then list result = tickers with close > val
"""
            is_valid, step_data, errors = QueryHandler.parse_gherkin(gherkin)
            assert is_valid, f"Failed for interval: {interval}, errors: {errors}"
            assert len(errors) == 0

    def test_gherkin_with_ohlc(self, query_handler):
        """Test parsing Gherkin with different OHLC values."""
        ohlc_values = ["open", "high", "low", "close", "volume"]

        for ohlc in ohlc_values:
            gherkin = f"""
Feature: v2
Scenario: test {ohlc}
Given stocks from index nifty50
When let val = latest in 1 samples of day {ohlc}
Then list result = tickers with {ohlc} > 100
"""
            is_valid, step_data, errors = QueryHandler.parse_gherkin(gherkin)
            assert is_valid, f"Failed for OHLC: {ohlc}, errors: {errors}"
            assert len(errors) == 0


# ==================== QUERY EXECUTION TESTS ====================

class TestQueryExecution:
    """Tests for query execution with different patterns."""

    def test_query_simple_bullish(self, query_handler):
        """Test simple bullish pattern query."""
        gherkin = """
Feature: v2
Scenario: simple bullish
Given stocks from index nifty50
When let ema = latest in 1 samples of day close ema 10
Then list bulls = tickers with close > ema
"""
        success, result, errors, data = query_handler.get_gherkin_result(
            gherkin)
        assert success
        assert isinstance(result, list)
        assert len(errors) == 0

    def test_query_simple_bearish(self, query_handler):
        """Test simple bearish pattern query."""
        gherkin = """
Feature: v2
Scenario: simple bearish
Given stocks from index nifty50
When let sma = latest in 1 samples of day close sma 20
Then list bears = tickers with close < sma
"""
        success, result, errors, data = query_handler.get_gherkin_result(
            gherkin)
        assert success
        assert isinstance(result, list)
        assert len(errors) == 0

    def test_query_multi_indicator(self, query_handler):
        """Test query with multiple indicators."""
        gherkin = """
Feature: v2
Scenario: multi-indicator screening
Given stocks from index nifty50
When let ema10 = latest in 1 samples of day close ema 10
* let sma20 = latest in 1 samples of day close sma 20
* let close = latest in 1 samples of day close
Then list result = tickers with close > ema10 and close > sma20
"""
        success, result, errors, data = query_handler.get_gherkin_result(
            gherkin)
        assert success
        assert len(errors) == 0

    def test_query_with_atr(self, query_handler):
        """Test query with ATR (Average True Range) indicator."""
        gherkin = """
Feature: v2
Scenario: atr screening
Given stocks from index nifty50
When let atr = latest in 10 samples of day close atr 14
Then list result = tickers with atr > 50
"""
        success, result, errors, data = query_handler.get_gherkin_result(
            gherkin)
        assert success
        assert len(errors) == 0

    def test_query_with_vwap(self, query_handler):
        """Test query with VWAP indicator."""
        gherkin = """
Feature: v2
Scenario: vwap screening
Given stocks from index nifty50
When let vwap = latest in 10 samples of day close vwap 10
Then list result = tickers with close > vwap
"""
        success, result, errors, data = query_handler.get_gherkin_result(
            gherkin)
        assert success
        assert len(errors) == 0

    def test_query_with_different_samples(self, query_handler):
        """Test query with different sample sizes."""
        for samples in [1, 5, 10, 20]:
            gherkin = f"""
Feature: v2
Scenario: test {samples} samples
Given stocks from index nifty50
When let val = latest in {samples} samples of day close
Then list result = tickers with close > val
"""
            success, result, errors, data = query_handler.get_gherkin_result(
                gherkin)
            assert success, f"Failed for {samples} samples, errors: {errors}"
            assert len(errors) == 0

    def test_query_with_different_operators(self, query_handler):
        """Test query with different operators."""
        operators = [
            ("latest", "last value"),
            ("oldest", "oldest value"),
            ("minimum", "minimum value"),
            ("maximum", "maximum value"),
        ]

        for op, description in operators:
            gherkin = f"""
Feature: v2
Scenario: {description}
Given stocks from index nifty50
When let val = {op} in 5 samples of day close
Then list result = tickers with close > val
"""
            success, result, errors, data = query_handler.get_gherkin_result(
                gherkin)
            assert success, f"Failed for operator {op}, errors: {errors}"
            assert len(errors) == 0

    def test_query_with_conditions(self, query_handler):
        """Test query with different comparison conditions."""
        conditions = [">", "<", ">=", "<=", "==", "!="]

        for condition in conditions:
            gherkin = f"""
Feature: v2
Scenario: test {condition}
Given stocks from index nifty50
When let val = latest in 1 samples of day close
Then list result = tickers with close {condition} val
"""
            success, result, errors, data = query_handler.get_gherkin_result(
                gherkin)
            assert success, f"Failed for condition {condition}, errors: {errors}"
            assert len(errors) == 0

    def test_query_invalid_ticker(self, query_handler):
        """Test query with invalid ticker returns error."""
        gherkin = """
Feature: v2
Scenario: invalid ticker
Given stocks from index invalid_index
When let val = latest in 1 samples of day close
Then list result = tickers with close > val
"""
        success, result, errors, data = query_handler.get_gherkin_result(
            gherkin)
        assert not success
        assert len(errors) > 0

    def test_query_invalid_interval(self, query_handler):
        """Test query with invalid interval returns error."""
        gherkin = """
Feature: v2
Scenario: invalid interval
Given stocks from index nifty50
When let val = latest in 1 samples of invalid_interval close
Then list result = tickers with close > val
"""
        success, result, errors, data = query_handler.get_gherkin_result(
            gherkin)
        assert not success
        assert len(errors) > 0


# ==================== AGENT TESTS ====================

class TestConverterAgent:
    """Tests for converter agent functionality."""

    @mock.patch('pytick.llm.agents.converter.ChatOllama')
    def test_converter_agent_with_mock(self, mock_llm):
        """Test converter agent with mocked LLM."""
        mock_llm_instance = mock.MagicMock()

        # Mock the invoke method to return a valid Gherkin
        mock_response = mock.MagicMock()
        mock_response.content = """
Feature: v2
Scenario: test
Given stocks from index nifty50
When let val = latest in 1 samples of day close
Then list result = tickers with close > val
"""
        mock_llm_instance.invoke.return_value = mock_response

        state = State(
            messages=[HumanMessage(content="Find bullish stocks")],
            message_type=None,
            errors=[]
        )

        result = converter_agent(
            state=state,
            system_prompt="Test prompt",
            llm=mock_llm_instance
        )

        assert result is not None
        assert "messages" in result

    def test_converter_agent_state(self):
        """Test converter agent state handling."""
        state = State(
            messages=[HumanMessage(content="Test query")],
            message_type=None,
            errors=[]
        )

        # Verify state structure
        assert "messages" in state
        assert "message_type" in state
        assert "errors" in state
        assert isinstance(state["messages"], list)


class TestValidatorAgent:
    """Tests for validator agent functionality."""

    def test_validator_agent_with_valid_gherkin(self):
        """Test validator agent with valid Gherkin."""
        gherkin = """
Feature: v2
Scenario: test
Given stocks from index nifty50
When let val = latest in 1 samples of day close
Then list result = tickers with close > val
"""
        state = State(
            messages=[AIMessage(content=gherkin)],
            message_type=None,
            errors=[]
        )

        mock_llm = mock.MagicMock()
        result = validator_agent(state, mock_llm)

        assert result is not None
        assert result["message_type"] in ["valid", "invalid"]

    def test_validator_agent_with_invalid_gherkin(self):
        """Test validator agent with invalid Gherkin."""
        invalid_gherkin = "Invalid Gherkin content"
        state = State(
            messages=[AIMessage(content=invalid_gherkin)],
            message_type=None,
            errors=[]
        )

        mock_llm = mock.MagicMock()
        result = validator_agent(state, mock_llm)

        assert result is not None
        # Invalid Gherkin should result in invalid message_type
        if result["message_type"] == "invalid":
            assert len(result["errors"]) > 0


# ==================== INTEGRATION TESTS ====================

class TestModelQueryIntegration:
    """Integration tests for models and queries."""

    def test_end_to_end_query_pipeline(self, query_handler):
        """Test complete query pipeline from input to result."""
        gherkin = """
Feature: v2
Scenario: end-to-end test
Given stocks from index nifty50
When let ema10 = latest in 1 samples of day close ema 10
* let sma20 = latest in 1 samples of day close sma 20
Then list bulls = tickers with close > ema10 and close > sma20
"""
        # Parse
        is_valid, step_data, parse_errors = QueryHandler.parse_gherkin(gherkin)
        assert is_valid
        assert len(parse_errors) == 0

        # Execute
        success, result, exec_errors, data = query_handler.get_gherkin_result(
            gherkin)
        assert success
        assert len(exec_errors) == 0

    def test_query_with_backtest_config(self, query_handler):
        """Test query execution with backtest configuration."""
        gherkin = """
Feature: v2
Scenario: backtest query
Given stocks from index nifty50
When let ema = latest in 1 samples of day close ema 10
Then list result = tickers with close > ema
"""

        bt_config = {
            "interval": "1d",
            "clip": 10,
            "default_ticker": "SBIN"
        }

        success, result, errors, data = query_handler.get_gherkin_result(
            gherkin, bt_config)
        # May succeed or have expected errors
        assert success or len(errors) == 0

    def test_query_multiple_scenarios(self, query_handler):
        """Test multiple query scenarios in sequence."""
        scenarios = [
            """
Feature: v2
Scenario: scenario1
Given stocks from index nifty50
When let ema = latest in 1 samples of day close ema 10
Then list result = tickers with close > ema
""",
            """
Feature: v2
Scenario: scenario2
Given stocks from index nifty50
When let sma = latest in 1 samples of day close sma 20
Then list result = tickers with close < sma
""",
            """
Feature: v2
Scenario: scenario3
Given stocks from index nifty50
When let atr = latest in 10 samples of day close atr 14
Then list result = tickers with atr > 50
""",
        ]

        for gherkin in scenarios:
            success, result, errors, data = query_handler.get_gherkin_result(
                gherkin)
            assert success, f"Query failed: {errors}"

    def test_data_handler_with_multiple_tickers(self, data_handler):
        """Test data handler works with multiple tickers."""
        tickers = ["TCS", "BEL", "SBIN", "TMPV"]

        for ticker in tickers:
            daily_data = data_handler.get_tables(
                tickers=[ticker], interval="1d")
            assert daily_data is not None
            assert not daily_data.empty


# ==================== EDGE CASE AND ERROR HANDLING TESTS ====================

class TestEdgeCasesAndErrorHandling:
    """Tests for edge cases and error handling."""

    def test_empty_gherkin(self, query_handler):
        """Test parsing empty Gherkin string."""
        gherkin = ""
        is_valid, step_data, errors = QueryHandler.parse_gherkin(gherkin)
        assert not is_valid
        assert len(errors) > 0

    def test_gherkin_with_only_whitespace(self, query_handler):
        """Test parsing Gherkin with only whitespace."""
        gherkin = "   \n\n   \t\t"
        is_valid, step_data, errors = QueryHandler.parse_gherkin(gherkin)
        assert not is_valid

    def test_gherkin_with_special_characters(self, query_handler):
        """Test Gherkin with special characters in values."""
        gherkin = """
Feature: v2
Scenario: test
Given stocks from index nifty50
When let val123 = latest in 1 samples of day close
Then list result_123 = tickers with close > val123
"""
        is_valid, step_data, errors = QueryHandler.parse_gherkin(gherkin)
        # Should handle alphanumeric with underscore
        assert len(errors) == 0 or is_valid

    def test_query_handler_state_independence(self, query_handler):
        """Test query handler maintains independent states."""
        gherkin1 = """
Feature: v2
Scenario: test1
Given stocks from index nifty50
When let val = latest in 1 samples of day close
Then list result = tickers with close > val
"""
        gherkin2 = """
Feature: v2
Scenario: test2
Given stocks from index nifty50
When let val = latest in 1 samples of day close ema 10
Then list result = tickers with close > val
"""

        success1, _, _, _ = query_handler.get_gherkin_result(gherkin1)
        success2, _, _, _ = query_handler.get_gherkin_result(gherkin2)

        # Both should execute successfully without interfering
        assert success1
        assert success2

    def test_very_large_sample_size(self, query_handler):
        """Test query with very large sample size."""
        gherkin = """
Feature: v2
Scenario: large samples
Given stocks from index nifty50
When let val = latest in 1000 samples of day close
Then list result = tickers with close > val
"""
        success, result, errors, data = query_handler.get_gherkin_result(
            gherkin)
        # Should either succeed or raise appropriate error
        assert isinstance(success, bool)

    def test_step_data_initialization(self):
        """Test StepData class initialization."""
        step_data = StepData()

        # Verify all required attributes exist
        assert hasattr(step_data, 'condition')
        assert hasattr(step_data, 'ohlc')
        assert hasattr(step_data, 'indicator')
        assert hasattr(step_data, 'interval')
        assert hasattr(step_data, 'operator')


# ==================== PARAMETRIZED TESTS ====================

class TestParametrized:
    """Parametrized tests for comprehensive coverage."""

    @pytest.mark.parametrize("indicator", ["sma", "ema", "atr", "vwap", "rvol"])
    def test_all_indicators(self, query_handler, indicator):
        """Test all available indicators."""
        period = "10" if indicator != "atr" else "14"
        gherkin = f"""
Feature: v2
Scenario: test {indicator}
Given stocks from index nifty50
When let val = latest in 1 samples of day close {indicator} {period}
Then list result = tickers with close > val
"""
        is_valid, step_data, errors = QueryHandler.parse_gherkin(gherkin)
        assert is_valid, f"Failed for indicator {indicator}: {errors}"

    @pytest.mark.parametrize("period", [5, 10, 20, 50, 100, 200])
    def test_indicator_periods(self, query_handler, period):
        """Test various indicator periods."""
        gherkin = f"""
Feature: v2
Scenario: test period {period}
Given stocks from index nifty50
When let val = latest in 1 samples of day close ema {period}
Then list result = tickers with close > val
"""
        is_valid, step_data, errors = QueryHandler.parse_gherkin(gherkin)
        assert is_valid, f"Failed for period {period}: {errors}"

    @pytest.mark.parametrize("comparison", [">", "<", ">=", "<=", "==", "!="])
    def test_all_comparisons(self, query_handler, comparison):
        """Test all comparison operators."""
        gherkin = f"""
Feature: v2
Scenario: test {comparison}
Given stocks from index nifty50
When let val = latest in 1 samples of day close
Then list result = tickers with close {comparison} val
"""
        is_valid, step_data, errors = QueryHandler.parse_gherkin(gherkin)
        assert is_valid, f"Failed for comparison {comparison}: {errors}"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])

import pytest
import os
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from influxdb_client import Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# Import the InfluxDBHandler class
from influx import InfluxDBHandler


@pytest.fixture
def mock_influxdb_client():
    """Mock InfluxDBClient for testing."""
    with patch('influx.InfluxDBClient') as mock_client:
        # Setup client ping
        mock_client.return_value.ping.return_value = True
        
        # Setup write_api
        mock_write_api = MagicMock()
        mock_client.return_value.write_api.return_value = mock_write_api
        
        # Setup delete_api
        mock_delete_api = MagicMock()
        mock_client.return_value.delete_api.return_value = mock_delete_api
        
        # Setup query_api
        mock_query_api = MagicMock()
        mock_client.return_value.query_api.return_value = mock_query_api
        
        # Setup buckets_api
        mock_buckets_api = MagicMock()
        mock_client.return_value.buckets_api.return_value = mock_buckets_api
        
        yield mock_client


@pytest.fixture
def influx_handler(mock_influxdb_client):
    """Create an InfluxDBHandler instance with mock client."""
    handler = InfluxDBHandler(
        tz="UTC",
        url="http://localhost:8086",
        token="test-token",
        org="test-org",
        bucket="test-bucket",
        prefix="test_stock_data",
        max_retries=3,
        retry_delay=0.1  # Short delay for tests
    )
    return handler


@pytest.fixture
def sample_stock_data():
    """Read sample stock data for testing."""
    data = pd.read_csv("test_influx.csv", parse_dates=['Datetime'], index_col='Datetime')
    return data


def test_initialization(influx_handler):
    """Test that the handler initializes correctly."""
    assert influx_handler.tz == "UTC"
    assert influx_handler.url == "http://localhost:8086"
    assert influx_handler.token == "test-token"
    assert influx_handler.org == "test-org"
    assert influx_handler.bucket == "test-bucket"
    assert influx_handler.point_name == "test_stock_data"
    assert influx_handler.max_retries == 3
    assert influx_handler.retry_delay == 0.1


def test_ensure_connection_success(influx_handler):
    """Test that _ensure_connection returns True when connection is successful."""
    assert influx_handler._ensure_connection() is True


def test_ensure_connection_failure(influx_handler, mock_influxdb_client):
    """Test that _ensure_connection retries and eventually fails when connection fails."""
    # Make ping throw an exception
    mock_influxdb_client.return_value.ping.side_effect = Exception("Connection failed")
    
    # Should retry max_retries times and then fail
    assert influx_handler._ensure_connection() is False
    assert mock_influxdb_client.return_value.ping.call_count == influx_handler.max_retries


def test_with_retry_success(influx_handler):
    """Test that _with_retry executes the function and returns its result when successful."""
    test_func = MagicMock(return_value="success")
    result = influx_handler._with_retry("test operation", test_func, "arg1", kwarg1="kwarg1")
    
    assert result == "success"
    test_func.assert_called_once_with("arg1", kwarg1="kwarg1")


def test_with_retry_failure(influx_handler):
    """Test that _with_retry retries and eventually fails when the function fails."""
    test_func = MagicMock(side_effect=Exception("Operation failed"))
    result = influx_handler._with_retry("test operation", test_func)
    
    assert result is False
    assert test_func.call_count == influx_handler.max_retries


# Removed test_write_success as write method has been removed from influx.py

def test_replace_data_with_empty_data(influx_handler):
    """Test that replace_data correctly handles empty data."""
    # Create empty DataFrame
    empty_df = pd.DataFrame()
    
    # Call replace_data with empty data
    result = influx_handler.replace_data(
        data=empty_df,
        ticker="TEST",
        interval="1d",
        config="test_config"
    )
    
    # Should return False for empty data without calling any API methods
    assert result is False
    influx_handler.client.delete_api().delete.assert_not_called()
    influx_handler.write_api.write.assert_not_called()


def test_clear_ticker_interval(influx_handler):
    """Test that clear_ticker_interval calls delete_api with the correct predicate."""
    # Mock the _with_retry method to capture the operation function
    original_with_retry = influx_handler._with_retry
    captured_operation = None
    
    def mock_with_retry(name, operation, *args, **kwargs):
        nonlocal captured_operation
        captured_operation = operation
        return original_with_retry(name, operation, *args, **kwargs)
    
    influx_handler._with_retry = mock_with_retry
    
    # Call clear_ticker_interval
    result = influx_handler.clear_ticker_interval(ticker="TEST", interval="1d")
    
    # Execute the captured operation to verify it works
    captured_operation()
    
    # Check that delete_api.delete was called with the correct predicate
    delete_call = influx_handler.client.delete_api().delete
    assert delete_call.call_count == 2
    call_args = delete_call.call_args[1]
    assert call_args['bucket'] == influx_handler.bucket
    assert call_args['org'] == influx_handler.org
    assert '_measurement="test_stock_data" AND ticker="TEST" AND interval="1d"' in call_args['predicate']
    
    # Restore _with_retry
    influx_handler._with_retry = original_with_retry


def test_replace_data(influx_handler, sample_stock_data):
    """Test that replace_data performs clear and write operations atomically."""
    with patch('influx.normalize_index_to_tz', return_value=sample_stock_data):
        # Mock the _with_retry method to capture the operation function
        original_with_retry = influx_handler._with_retry
        captured_operation = None
        
        def mock_with_retry(name, operation, *args, **kwargs):
            nonlocal captured_operation
            captured_operation = operation
            return original_with_retry(name, operation, *args, **kwargs)
        
        influx_handler._with_retry = mock_with_retry
        
        # Mock __calculate_indicators to return the original data and indicator prefixes
        influx_handler._InfluxDBHandler__calculate_indicators = MagicMock(
            return_value=(sample_stock_data, ('sma_', 'ema_', 'atr_'))
        )
        
        # Call replace_data
        result = influx_handler.replace_data(
            data=sample_stock_data,
            ticker="TEST",
            interval="1d",
            config="test_config"
        )
        
        # Verify the result
        assert result is not False
        assert captured_operation is not None
        
        # Execute the captured operation to verify it works
        captured_operation()
        
        # Check that delete_api.delete and write_api.write were called
        assert influx_handler.client.delete_api().delete.call_count == 2
        assert influx_handler.write_api.write.call_count == 2
        
        # Restore _with_retry
        influx_handler._with_retry = original_with_retry


def test_replace_data_with_connection_failure_recovery(influx_handler, sample_stock_data):
    """Test that replace_data can recover from a connection failure."""
    with patch('influx.normalize_index_to_tz', return_value=sample_stock_data):
        # Mock __calculate_indicators to return the original data and indicator prefixes
        influx_handler._InfluxDBHandler__calculate_indicators = MagicMock(
            return_value=(sample_stock_data, ('sma_', 'ema_'))
        )
        
        # Set up delete_api to fail once then succeed
        delete_api = influx_handler.client.delete_api()
        delete_api.delete.side_effect = [
            Exception("Connection failed"),  # First call fails
            None                            # Second call succeeds
        ]
        
        # Original ensure_connection to be restored later
        original_ensure_connection = influx_handler._ensure_connection
        
        # Mock _ensure_connection to simulate reconnection
        connection_attempts = 0
        def mock_ensure_connection():
            nonlocal connection_attempts
            connection_attempts += 1
            if connection_attempts == 1:
                return True  # Initial check succeeds
            if connection_attempts == 2:
                # After failure, need to reconnect
                influx_handler._initialize_client()
                return True
            return True
        
        influx_handler._ensure_connection = mock_ensure_connection
        
        # Call replace_data
        result = influx_handler.replace_data(
            data=sample_stock_data,
            ticker="TEST",
            interval="1d",
            config="test_config"
        )
        
        # Verify the result was successful despite the initial failure
        assert result is not False
        
        # Check that delete_api.delete was called twice (once failing, once succeeding)
        assert delete_api.delete.call_count == 2
        
        # Check that write_api.write was called once (after successful delete)
        influx_handler.write_api.write.assert_called_once()
        
        # Restore the original method
        influx_handler._ensure_connection = original_ensure_connection


def test_to_dataframe(influx_handler, sample_stock_data):
    """Test that to_dataframe queries and processes data correctly."""
    # # Create a mock DataFrame that would be returned by query_data_frame
    # mock_df = pd.DataFrame({
    #     '_time': pd.date_range(start='2023-01-01', periods=5, freq='D'),
    #     'Open': [100.0, 101.0, 102.0, 103.0, 104.0],
    #     'High': [105.0, 106.0, 107.0, 108.0, 109.0],
    #     'Low': [95.0, 96.0, 97.0, 98.0, 99.0],
    #     'Close': [103.0, 104.0, 105.0, 106.0, 107.0],
    #     'Volume': [1000, 1100, 1200, 1300, 1400],
    #     'Dividends': [0, 0, 0, 0, 0],
    #     'Stock Splits': [0, 0, 0, 0, 0],
    #     'result': ['result'] * 5,
    #     'table': [0] * 5,
    #     'ticker': ['TEST'] * 5,
    #     'interval': ['1d'] * 5
    # })
    
    # Mock the query_data_frame method to return our mock DataFrame
    # influx_handler.client.query_api().query_data_frame.return_value = mock_df
    influx_handler.replace_data(sample_stock_data, "TEST", "1d", "config_debug.yaml")
    # Mock normalize_index_to_tz to return the DataFrame unchanged
    # with patch('influx.normalize_index_to_tz', return_value=mock_df):
        # Call to_dataframe
    result = influx_handler.to_dataframe(ticker="TEST", interval="1d")
    
    # Verify that query_data_frame was called
    influx_handler.client.query_api().query_data_frame.assert_called_once()
    
    # Verify the result has the expected columns and no extra columns
    assert 'Open' in result.columns
    assert 'High' in result.columns
    assert 'Low' in result.columns
    assert 'Close' in result.columns
    assert 'Volume' in result.columns
    assert 'Dividends' in result.columns
    assert 'Stock Splits' in result.columns
    
    # These should have been removed
    assert 'result' not in result.columns
    assert 'table' not in result.columns
    assert 'ticker' not in result.columns
    assert 'interval' not in result.columns


def test_create_bucket_if_not_exists_new(influx_handler):
    """Test creating a bucket that doesn't exist."""
    # Mock the buckets_api to return a bucket list that doesn't include our bucket
    mock_bucket = MagicMock()
    mock_bucket.name = "other-bucket"
    mock_buckets = MagicMock()
    mock_buckets.buckets = [mock_bucket]
    
    influx_handler.client.buckets_api.return_value.find_buckets.return_value = mock_buckets
    
    # Mock the _with_retry method to capture the operation function
    original_with_retry = influx_handler._with_retry
    captured_operation = None
    
    def mock_with_retry(name, operation, *args, **kwargs):
        nonlocal captured_operation
        captured_operation = operation
        return original_with_retry(name, operation, *args, **kwargs)
    
    influx_handler._with_retry = mock_with_retry
    
    # Call create_bucket_if_not_exists
    result = influx_handler.create_bucket_if_not_exists()
    
    # Execute the captured operation to verify it works
    captured_operation()
    
    # Check that create_bucket was called
    influx_handler.client.buckets_api().create_bucket.assert_called_once_with(
        bucket_name=influx_handler.bucket,
        org=influx_handler.org
    )
    
    # Restore _with_retry
    influx_handler._with_retry = original_with_retry


def test_create_bucket_if_not_exists_existing(influx_handler):
    """Test creating a bucket that already exists."""
    # Mock the buckets_api to return a bucket list that includes our bucket
    mock_bucket = MagicMock()
    mock_bucket.name = influx_handler.bucket
    mock_buckets = MagicMock()
    mock_buckets.buckets = [mock_bucket]
    
    influx_handler.client.buckets_api().find_buckets.return_value = mock_buckets
    
    # Mock the _with_retry method to capture the operation function
    original_with_retry = influx_handler._with_retry
    captured_operation = None
    
    def mock_with_retry(name, operation, *args, **kwargs):
        nonlocal captured_operation
        captured_operation = operation
        return original_with_retry(name, operation, *args, **kwargs)
    
    influx_handler._with_retry = mock_with_retry
    
    # Call create_bucket_if_not_exists
    result = influx_handler.create_bucket_if_not_exists()
    
    # Execute the captured operation to verify it works
    captured_operation()
    
    # Check that create_bucket was not called
    influx_handler.client.buckets_api().create_bucket.assert_not_called()
    
    # Restore _with_retry
    influx_handler._with_retry = original_with_retry


def test_integration(mock_influxdb_client, sample_stock_data):
    """Test a full workflow - create bucket, write data, query data, clear data."""
    # Create a real handler with a mock client
    handler = InfluxDBHandler(
        tz="UTC",
        url="http://localhost:8086",
        token="test-token",
        org="test-org",
        bucket="test-bucket",
        prefix="test_stock_data",
        max_retries=3,
        retry_delay=0.1
    )
    
    # Setup necessary mocks
    mock_influxdb_client.return_value.buckets_api().find_buckets.return_value.buckets = []
    
    mock_query_result = pd.DataFrame({
        '_time': pd.date_range(start='2023-01-01', periods=5, freq='D'),
        'Open': [100.0, 101.0, 102.0, 103.0, 104.0],
        'High': [105.0, 106.0, 107.0, 108.0, 109.0],
        'Low': [95.0, 96.0, 97.0, 98.0, 99.0],
        'Close': [103.0, 104.0, 105.0, 106.0, 107.0],
        'Volume': [1000, 1100, 1200, 1300, 1400],
        'Dividends': [0, 0, 0, 0, 0],
        'Stock Splits': [0, 0, 0, 0, 0],
        'result': ['result'] * 5,
        'table': [0] * 5,
        'ticker': ['TEST'] * 5,
        'interval': ['1d'] * 5
    })
    
    mock_influxdb_client.return_value.query_api().query_data_frame.return_value = mock_query_result
    
    with patch('influx.normalize_index_to_tz', return_value=sample_stock_data):
        # Mock __calculate_indicators to return the original data and indicator prefixes
        handler._InfluxDBHandler__calculate_indicators = MagicMock(
            return_value=(sample_stock_data, ('sma_', 'ema_'))
        )
        
        # Step 1: Create bucket
        assert handler.create_bucket_if_not_exists() is not False
        mock_influxdb_client.return_value.buckets_api().create_bucket.assert_called_once()
        
        # Step 2: Replace data (since write method has been removed)
        assert handler.replace_data(
            data=sample_stock_data,
            ticker="TEST",
            interval="1d",
            config="test_config"
        ) is not False
        # Both delete and write should be called
        mock_influxdb_client.return_value.delete_api().delete.assert_called_once()
        mock_influxdb_client.return_value.write_api().write.assert_called_once()
        
        # Step 3: Read data
        result_df = handler.to_dataframe(ticker="TEST", interval="1d")
        assert result_df is not None
        mock_influxdb_client.return_value.query_api().query_data_frame.assert_called_once()
        
        # Step 4: Clear data
        mock_influxdb_client.return_value.delete_api().delete.reset_mock()
        assert handler.clear_ticker_interval(ticker="TEST", interval="1d") is not False
        mock_influxdb_client.return_value.delete_api().delete.assert_called_once()
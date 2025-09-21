import logging
import multiprocessing
import pandas as pd
import yfinance as yf
import pandas_ta as ta

# from main import mp_process_ticker
from utility import get_logger, read_config

logger = get_logger('yf', logging.DEBUG)

def download_stock_data(ticker:str, interval:str, tz:str)->pd.DataFrame:
    ticker_symbol = f"{ticker}{".NS" if tz=="Asia/Kolkata" else ""}"
    data = yf.download(
        tickers=[ticker_symbol],
        period="max",
        interval=interval,
        progress=False,
        group_by="ticker",
        rounding=True,
        actions=True,
        threads=True,
        multi_level_index=False,
        ignore_tz=True,
        auto_adjust=True,
    )
    return data

def calculate_indicators(ticker:str, df: pd.DataFrame, indicators:dict) -> dict:
    for ind_type, ind_conf in indicators.items():
        periods = ind_conf.get('periods', [])
        sources = ind_conf.get('sources', [])
        for src in sources:
            src_col = src.lower() if src.lower() in df.columns else src.capitalize()
            for period in periods:
                try:
                    col_name = f"{ind_type}_{period}_{src}"
                    if ind_type == 'sma':
                        df[col_name] = ta.sma(df[src_col], length=period).round(2)
                    elif ind_type == 'ema':
                        df[col_name] = ta.ema(df[src_col], length=period).round(2)
                    elif ind_type == 'atr':
                        df[col_name] = ta.atr(df['High'], df['Low'], df['Close'], length=period).round(2)
                    else:
                        logger.warning(f"Unsupported indicator type: {ind_type}")
                except Exception as e:
                    logger.error(f"Error calculating {ind_type} for period {period} and source {src}: {e}")
    return {'ticker': ticker, 'df' : df}

def get_tickers_table(tickers: list, interval: str, tz: str, indicators: dict) -> pd.DataFrame:
    tickers_yf = [f"{ticker}{'.NS' if tz=='Asia/Kolkata' else ''}" for ticker in tickers]
    ohlc = yf.download(
        tickers=tickers_yf,
        period="max",
        interval=interval,
        progress=False,
        group_by="ticker",
        rounding=True,
        actions=True,
        threads=True,
        multi_level_index=False,
        ignore_tz=True,
        auto_adjust=True,
    )
    clean_ohlc = {}
    for ticker in tickers_yf:
        df = ohlc[ticker] #.xs(ticker, axis=1, level=0)
        df = df.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'], how='all')
        if df.empty:
            logger.warning(f"No data found for ticker: {ticker}")
        clean_ohlc[ticker] = df  # if you want to store back

    # Create a pool of processes (one for each CPU core)
    num_processes = min(multiprocessing.cpu_count(), len(tickers))
    # Prepare the parameters for each process
    process_args = [
        (ticker, clean_ohlc[ticker], indicators)
        for ticker in tickers_yf
    ]
    result = {}
    # Use a process pool executor for true parallelism
    with multiprocessing.Pool(processes=num_processes) as pool:
        # Map the processing function to all tickers with their parameters
        results = pool.starmap(calculate_indicators, process_args)

    for point in results:
        ticker = point['ticker'].split('.')[0]
        df = point['df']
        result[ticker] = df
        if df is None or df.empty:
            logger.warning(f"No data found for ticker: {ticker}")
    
    return result

def get_nifty50_tickers() -> list:
    nifty50 = pd.read_csv('ind_nifty50list.csv')
    return nifty50['Symbol'].tolist()

if __name__ == "__main__":
    # config_path = "config_debug.yaml"
    # indicators = read_config(config_path).get('indicators', {})
    # get_tickers_table(["BEL", "TCS", "HONASA"], "1d", "Asia/Kolkata", indicators)
    print(get_nifty50_tickers())
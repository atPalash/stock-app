import yaml
import logging
import pandas as pd

def read_config(file_path):
    logger = get_logger('utility', logging.DEBUG)
    try:
        with open(file_path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error reading config file: {e}")
        return e

def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Get a logger configured to log to the console.

    :param name: The name of the logger, usually `__name__`.
    :param level: The logging level (default is INFO).
    :return: Configured Logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        logger.setLevel(level)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

    return logger

def normalize_index_to_tz(df, tz_str='Asia/Kolkata'):
    """
    Normalize DataFrame index to tz-aware with the given timezone.
    Handles both tz-naive and tz-aware indices.
    """
    df.index = pd.to_datetime(df.index, errors='coerce')
    if getattr(df.index, 'tz', None) is None:
        df.index = df.index.tz_localize(tz_str)
    else:
        df.index = df.index.tz_convert(tz_str)
    return df
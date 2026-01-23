import sys
import yaml
import logging
import pandas as pd
import fcntl

def read_config(file_path):
    logger = get_logger('utility', logging.DEBUG)
    try:
        with open(file_path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"Exception reading config file {file_path}: {e}")
        return e

def save_config(key:str, data:dict, path:str):   
    # Save the dictionary to a YAML file
    to_write = read_config(path)
    with open(path, "w") as file:
        fcntl.flock(file, fcntl.LOCK_EX)
        if key is None:
            to_write = data
        else:
            to_write[key] = data
        yaml.dump(to_write, file, default_style='"')
        fcntl.flock(file, fcntl.LOCK_UN)
        
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
        console_handler.setStream(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

    return logger

def normalize_index_to_tz(df, tz_str):
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

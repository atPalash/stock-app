import logging


def get_logger(name: str, level=logging.ERROR) -> logging.Logger:
    # Create a logger with the specified name
    logger = logging.getLogger(name)
    # Set the default logging level
    logger.setLevel(level)

    # Create a console handler if not already added (to avoid duplicate handlers)
    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.ERROR)

        # Define the logging format
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(formatter)

        # Add the handler to the logger
        logger.addHandler(console_handler)

    return logger

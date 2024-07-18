import logging
from logging.handlers import RotatingFileHandler
import os
import gzip
import sys

def namer(name):
    return name + ".gz"

def rotator(source, dest):
    with open(source, "rb") as sf:
        with gzip.open(dest, "wb") as df:
            df.writelines(sf)
    os.remove(source)

def setup_logger(app, log_file, level=logging.DEBUG):
    """Function to set up a logger with file and console handlers"""
    # Ensure logs directory exists
    logs_dir = 'logs'
    os.makedirs(logs_dir, exist_ok=True)

    # Use Flask's built-in logger
    logger = app.logger
    logger.setLevel(level)

    # Create handlers
    c_handler = logging.StreamHandler()
    f_handler = RotatingFileHandler(
        os.path.join(logs_dir, log_file),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        mode='a',
        encoding='utf-8'
    )
    c_handler.setLevel(logging.INFO)  # Console logs at INFO level
    f_handler.setLevel(logging.DEBUG)  # File logs at DEBUG level

    # Set up rotation
    f_handler.rotator = rotator
    f_handler.namer = namer

    # Create formatters and add them to handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(formatter)
    f_handler.setFormatter(formatter)

    # Add handlers to the Flask logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)
    logger.info("Logging setup complete.")

    return logger

# Create the main app logger
logger = setup_logger('rss_manager', 'app.log')

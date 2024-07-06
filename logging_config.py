import logging
from logging.handlers import RotatingFileHandler
import os
import gzip

def namer(name):
    return name + ".gz"

def rotator(source, dest):
    with open(source, "rb") as sf:
        with gzip.open(dest, "wb") as df:
            df.writelines(sf)
    os.remove(source)

# Ensure logs directory exists
logs_dir = 'logs'
os.makedirs(logs_dir, exist_ok=True)

# Create a custom logger
logger = logging.getLogger('rss_manager')
logger.setLevel(logging.DEBUG)

# Create handlers
c_handler = logging.StreamHandler()
f_handler = RotatingFileHandler(
    os.path.join(logs_dir, 'app.log'),
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    mode='a'
)
c_handler.setLevel(logging.WARNING)
f_handler.setLevel(logging.DEBUG)

# Set up rotation
f_handler.rotator = rotator
f_handler.namer = namer

# Create formatters and add them to handlers
c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
c_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)

# Add handlers to the logger
logger.addHandler(c_handler)
logger.addHandler(f_handler)

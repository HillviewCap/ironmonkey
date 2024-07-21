from logging_config import setup_logger

# Create a separate logger for RSS manager
logger = setup_logger('rss_manager', 'rss_manager.log')

PER_PAGE_OPTIONS = [10, 25, 50, 100]

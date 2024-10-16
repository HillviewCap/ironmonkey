import time
import random
from functools import wraps
import logging

logger = logging.getLogger(__name__)

def retry_with_backoff(max_retries=5, base_delay=1, max_delay=60):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if "429" not in str(e):
                        raise
                    
                    retries += 1
                    if retries == max_retries:
                        logger.error(f"Max retries reached for {func.__name__}")
                        raise

                    delay = min(base_delay * (2 ** retries) + random.uniform(0, 1), max_delay)
                    logger.warning(f"Rate limit hit. Retrying in {delay:.2f} seconds...")
                    time.sleep(delay)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

import os
import time
from functools import wraps

LOCK_FILE = 'database.lock'

def acquire_lock():
    while os.path.exists(LOCK_FILE):
        time.sleep(0.1)
    with open(LOCK_FILE, 'w') as f:
        f.write('locked')
    return LOCK_FILE

def release_lock(lock_file):
    if os.path.exists(lock_file):
        os.remove(lock_file)

def is_database_locked():
    return os.path.exists(LOCK_FILE)

def with_lock(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        lock = acquire_lock()
        try:
            return func(*args, **kwargs)
        finally:
            release_lock(lock)
    return wrapper

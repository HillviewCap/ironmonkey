from sqlalchemy.pool import QueuePool
from app.extensions import db

def setup_db_pool():
    engine = db.get_engine()
    engine.dispose()
    db.engine = engine.execution_options(
        pool_size=10,
        max_overflow=20,
        pool_recycle=1800,
        pool_pre_ping=True,
        pool_use_lifo=True
    )

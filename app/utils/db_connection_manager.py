from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask import current_app
from contextlib import contextmanager

class DBConnectionManager:
    _engine = None
    _session_factory = None

    @classmethod
    def initialize(cls, app):
        cls._engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'], pool_size=10, max_overflow=20)
        cls._session_factory = scoped_session(sessionmaker(bind=cls._engine))

    @classmethod
    @contextmanager
    def get_session(cls):
        session = cls._session_factory()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

def init_db_connection_manager(app):
    DBConnectionManager.initialize(app)

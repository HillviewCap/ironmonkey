from __future__ import annotations
from gremlin_python.driver.client import Client
from typing import Optional

class GraphConnectionManager:
    _client: Optional[Client] = None

    @classmethod
    def initialize(cls, app):
        graph_db_host = app.config.get('GRAPH_DB_HOST')
        if not graph_db_host:
            app.logger.warning('Graph database host not set. Skipping graph client initialization.')
            cls._client = None
            return
        cls._client = Client(f'wss://{graph_db_host}:8182/gremlin', 'g')

    @classmethod
    def get_client(cls) -> Client:
        return cls._client

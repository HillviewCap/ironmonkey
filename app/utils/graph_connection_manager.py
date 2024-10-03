from __future__ import annotations
from gremlin_python.driver.client import Client
from typing import Optional

class GraphConnectionManager:
    _client: Optional[Client] = None

    @classmethod
    def initialize(cls, app):
        graph_db_url = app.config.get('GRAPH_DB_URL')
        if not graph_db_url:
            app.logger.warning('Graph database URL not set. Skipping graph client initialization.')
            cls._client = None
            return
        cls._client = Client(graph_db_url, 'g')

    @classmethod
    def get_client(cls) -> Client:
        return cls._client

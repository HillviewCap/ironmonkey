from __future__ import annotations
from gremlin_python.driver import Client
from typing import Optional

class GraphConnectionManager:
    _client: Optional[Client] = None

    @classmethod
    def initialize(cls, app):
        cls._client = Client('wss://<your-graph-db-host>:8182/gremlin', 'g')

    @classmethod
    def get_client(cls) -> Client:
        return cls._client

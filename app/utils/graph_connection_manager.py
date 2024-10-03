from __future__ import annotations
from neo4j import GraphDatabase
from typing import Optional

class GraphConnectionManager:
    _driver: Optional[GraphDatabase.driver] = None

    @classmethod
    def initialize(cls, app):
        neo4j_uri = app.config.get('NEO4J_URI')
        neo4j_user = app.config.get('NEO4J_USER')
        neo4j_password = app.config.get('NEO4J_PASSWORD')
        if not neo4j_uri or not neo4j_user or not neo4j_password:
            app.logger.warning('Neo4j configuration not set. Skipping graph client initialization.')
            cls._driver = None
            return
        cls._driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

    @classmethod
    def get_driver(cls):
        return cls._driver

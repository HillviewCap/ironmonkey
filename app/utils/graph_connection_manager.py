from __future__ import annotations
from neo4j import GraphDatabase
from typing import Optional
import logging

class GraphConnectionManager:
    _driver: Optional[GraphDatabase.driver] = None

    logger = logging.getLogger('graph_connection_manager')
    logger.setLevel(logging.DEBUG)  # Set log level to DEBUG

    @classmethod
    def initialize(cls, app):
        neo4j_uri = app.config.get('NEO4J_URI')
        neo4j_user = app.config.get('NEO4J_USER')
        neo4j_password = app.config.get('NEO4J_PASSWORD')
        logger.debug('Neo4j configuration: URI=%s, User=%s', neo4j_uri, neo4j_user)
        if not neo4j_uri or not neo4j_user or not neo4j_password:
            app.logger.warning('Neo4j configuration not set. Skipping graph client initialization.')
            cls._driver = None
            return
        try:
            logger.debug(f'Initializing Neo4j driver with URI: {neo4j_uri}')
            cls._driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
            logger.info('Neo4j driver initialized successfully.')
        except Exception as e:
            logger.exception('Failed to initialize Neo4j driver: %s', e)
            cls._driver = None

    @classmethod
    def get_driver(cls):
        return cls._driver

from __future__ import annotations
from neo4j import GraphDatabase
from typing import Optional
import logging

class GraphConnectionManager:
    _driver: Optional[GraphDatabase.driver] = None

    @classmethod

    @classmethod
    def initialize(cls, app):
        cls.logger = logging.getLogger('graph_connection_manager')
        cls.logger.setLevel(logging.DEBUG)  # Set log level to DEBUG

        neo4j_uri = app.config.get('NEO4J_URI')
        neo4j_user = app.config.get('NEO4J_USER')
        neo4j_password = app.config.get('NEO4J_PASSWORD')
        cls.logger.debug('Neo4j configuration: URI=%s, User=%s', neo4j_uri, neo4j_user)
        if not neo4j_uri or not neo4j_user or not neo4j_password:
            app.logger.warning('Neo4j configuration not set. Skipping graph client initialization.')
            cls._driver = None
            return
        try:
            cls.logger.debug(f'Initializing Neo4j driver with URI: {neo4j_uri}')
            cls._driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
            cls.logger.info('Neo4j driver initialized successfully.')
        except Exception as e:
            cls.logger.exception('Failed to initialize Neo4j driver: %s', e)
            cls._driver = None

    @classmethod
    def get_driver(cls):
        return cls._driver

    @classmethod
    def get_groups_tools_countries_graph(cls):
        driver = cls.get_driver()
        if driver is None:
            return None

        with driver.session() as session:
            result = session.run("""
                MATCH (g:Group)-[:HAS_VALUE]->(gv:GroupValue)-[:HAS_NAME]->(gn:GroupName)
                OPTIONAL MATCH (gv)-[:USES]->(t:Tool)
                RETURN g, gv, gn, t, g.country AS country
            """)
            
            nodes = []
            edges = []
            countries = set()

            for record in result:
                group = record['g']
                group_value = record['gv']
                group_name = record['gn']
                tool = record['t']
                country = record['country']

                nodes.append({"id": group['uuid'], "label": "Group", "name": group['name']})
                nodes.append({"id": group_value['uuid'], "label": "GroupValue", "name": group_value['actor']})
                nodes.append({"id": group_name['uuid'], "label": "GroupName", "name": group_name['name']})
                
                edges.append({"id": f"{group['uuid']}_has_value_{group_value['uuid']}", "outV": group['uuid'], "inV": group_value['uuid'], "label": "HAS_VALUE"})
                edges.append({"id": f"{group_value['uuid']}_has_name_{group_name['uuid']}", "outV": group_value['uuid'], "inV": group_name['uuid'], "label": "HAS_NAME"})

                if tool:
                    nodes.append({"id": tool['uuid'], "label": "Tool", "name": tool['name']})
                    edges.append({"id": f"{group_value['uuid']}_uses_{tool['uuid']}", "outV": group_value['uuid'], "inV": tool['uuid'], "label": "USES"})

                if country:
                    countries.add(country)

            for country in countries:
                country_id = f"country_{country}"
                nodes.append({"id": country_id, "label": "Country", "name": country})
                for node in nodes:
                    if node['label'] == "Group" and record['g']['country'] == country:
                        edges.append({"id": f"{node['id']}_from_{country_id}", "outV": node['id'], "inV": country_id, "label": "FROM"})

            return {"nodes": nodes, "edges": edges}

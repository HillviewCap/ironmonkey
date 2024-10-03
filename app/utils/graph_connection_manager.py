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
            node_ids = set()

            for record in result:
                group = record['g']
                group_value = record['gv']
                group_name = record['gn']
                tool = record['t']
                country = record['country']

                # Add nodes only if they don't already exist
                if group['uuid'] not in node_ids:
                    nodes.append({"data": {"id": group['uuid'], "label": "Group", "name": group['name']}})
                    node_ids.add(group['uuid'])

                if group_value['uuid'] not in node_ids:
                    nodes.append({"data": {"id": group_value['uuid'], "label": "GroupValue", "name": group_value['actor']}})
                    node_ids.add(group_value['uuid'])

                if group_name['uuid'] not in node_ids:
                    nodes.append({"data": {"id": group_name['uuid'], "label": "GroupName", "name": group_name['name']}})
                    node_ids.add(group_name['uuid'])
                
                edges.append({"data": {"id": f"{group['uuid']}_has_value_{group_value['uuid']}", "source": group['uuid'], "target": group_value['uuid'], "label": "HAS_VALUE"}})
                edges.append({"data": {"id": f"{group_value['uuid']}_has_name_{group_name['uuid']}", "source": group_value['uuid'], "target": group_name['uuid'], "label": "HAS_NAME"}})

                if tool:
                    if tool['uuid'] not in node_ids:
                        nodes.append({"data": {"id": tool['uuid'], "label": "Tool", "name": tool['name']}})
                        node_ids.add(tool['uuid'])
                    edges.append({"data": {"id": f"{group_value['uuid']}_uses_{tool['uuid']}", "source": group_value['uuid'], "target": tool['uuid'], "label": "USES"}})

                if country:
                    countries.add(country)

            for country in countries:
                country_id = f"country_{country}"
                if country_id not in node_ids:
                    nodes.append({"data": {"id": country_id, "label": "Country", "name": country}})
                    node_ids.add(country_id)
                for node in nodes:
                    if node['data']['label'] == "Group" and group['country'] == country:
                        edges.append({"data": {"id": f"{node['data']['id']}_from_{country_id}", "source": node['data']['id'], "target": country_id, "label": "FROM"}})

            return {"nodes": nodes, "edges": edges}

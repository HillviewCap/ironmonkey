"""
This module contains the API routes for the application.

It defines various endpoints for retrieving content, feeds, users,
and for summarizing content using the Ollama API.
"""

"""
This module contains the API routes for the application.

It defines various endpoints for retrieving content, feeds, users,
and for summarizing content using the Ollama API.
"""

from flask import Blueprint, jsonify, current_app
from neo4j.exceptions import ServiceUnavailable
from flask_login import login_required
from app.utils.graph_connection_manager import GraphConnectionManager
from gremlin_python.process.traversal import T

api_bp = Blueprint('api', __name__)

@api_bp.route('/v1/graph', methods=['GET'])
@login_required
def get_graph_data():
    driver = GraphConnectionManager.get_driver()
    if driver is None:
        return jsonify({'error': 'Graph database not available'}), 503

    nodes = []
    edges = []
    def fetch_data(tx):
        result_nodes = tx.run("MATCH (n) RETURN DISTINCT n")
        for record in result_nodes:
            node = record["n"]
            nodes.append({
                'data': {
                    'id': str(node['uuid']),
                    'label': list(node.labels)[0],
                    **node._properties
                }
            })
        result_edges = tx.run("MATCH (n)-[r]->(m) RETURN r")
        for record in result_edges:
            rel = record["r"]
            edges.append({
                'data': {
                    'id': str(rel.id),
                    'source': str(rel.start_node['uuid']),
                    'target': str(rel.end_node['uuid']),
                    'label': rel.type,
                }
            })

    try:
        with driver.session() as session:
            session.read_transaction(fetch_data)
    except ServiceUnavailable as e:
        current_app.logger.error(f'Neo4j Service Unavailable: {e}')
        return jsonify({'error': 'Neo4j database not available'}), 503

    return jsonify(nodes + edges)

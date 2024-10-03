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

from flask import Blueprint, jsonify
from flask_login import login_required
from app.utils.graph_connection_manager import GraphConnectionManager
from gremlin_python.process.traversal import T

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/v1/graph', methods=['GET'])
@login_required
def get_graph_data():
    client = GraphConnectionManager.get_client()
    # Fetch nodes
    vertices = client.submit("g.V().valueMap(true)").all().result()
    nodes = [
        {
            'data': {
                'id': str(v[T.id]),
                'label': v['label'][0],
                **{k: v[k][0] for k in v if k != 'label'}
            }
        }
        for v in vertices
    ]

    # Fetch edges
    edges_result = client.submit("g.E().elementMap()").all().result()
    edges = [
        {
            'data': {
                'id': str(e[T.id]),
                'source': str(e[T.outV]),
                'target': str(e[T.inV]),
                'label': e['label']
            }
        }
        for e in edges_result
    ]

    return jsonify({'nodes': nodes, 'edges': edges})

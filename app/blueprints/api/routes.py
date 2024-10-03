"""
This module contains the API routes for the application.

It defines various endpoints for retrieving content, feeds, users,
and for summarizing content using the Ollama API.
"""

from flask import Blueprint, jsonify, current_app
from app.models.relational.parsed_content import ParsedContent
from app.models.relational.rss_feed import RSSFeed
from app.extensions import db
from neo4j.exceptions import ServiceUnavailable
from flask_login import login_required
from app.utils.graph_connection_manager import GraphConnectionManager
from app.utils.logging_config import setup_logger

api_bp = Blueprint('api', __name__)

# Initialize logger for API routes
logger = setup_logger('api_routes', 'api_routes.log')

@api_bp.route('/v1/parsed_contents', methods=['GET'])
@login_required
def get_parsed_contents():
    parsed_contents = db.session.query(
        ParsedContent.id,
        ParsedContent.title,
        ParsedContent.url,
        ParsedContent.description,
        ParsedContent.content,
        ParsedContent.summary,
        ParsedContent.feed_id,
        ParsedContent.created_at,
        ParsedContent.pub_date,
        ParsedContent.creator,
        ParsedContent.art_hash,
        RSSFeed.title.label('feed_title')
    ).join(RSSFeed).filter(
        ParsedContent.title.isnot(None),
        ParsedContent.description.isnot(None)
    ).order_by(ParsedContent.pub_date.desc()).limit(6).offset(0).all()

    results = [dict(row) for row in parsed_contents]
    return jsonify(results)

@api_bp.route('/v1/graph', methods=['GET'])
@login_required
def get_graph_data():
    driver = GraphConnectionManager.get_driver()
    if driver is None:
        logger.error("Neo4j driver not initialized.")
        return jsonify({'error': 'Neo4j driver not initialized'}), 500

    with driver.session() as session:
        query = """
        MATCH (n)
        OPTIONAL MATCH (n)-[r]->(m)
        RETURN n, r, m
        """
        result = session.run(query)

        elements = []
        nodes_seen = set()

        for record in result:
            n = record['n']
            r = record.get('r')
            m = record.get('m')

            # Process node 'n'
            n_id = str(n.id)
            if n_id not in nodes_seen:
                nodes_seen.add(n_id)
                elements.append({
                    'data': {
                        'id': n_id,
                        'label': list(n.labels)[0],
                        **n._properties
                    }
                })

            # Process relationship 'r' and node 'm' if they exist
            if r and m:
                m_id = str(m.id)
                if m_id not in nodes_seen:
                    nodes_seen.add(m_id)
                    elements.append({
                        'data': {
                            'id': m_id,
                            'label': list(m.labels)[0],
                            **m._properties
                        }
                    })
                elements.append({
                    'data': {
                        'id': str(r.id),
                        'source': n_id,
                        'target': m_id,
                        'label': r.type
                    }
                })

    return jsonify(elements)

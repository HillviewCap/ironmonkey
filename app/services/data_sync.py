from __future__ import annotations
from app.models.relational.allgroups import AllGroups, AllGroupsValues
from app.models.relational.alltools import AllTools, AllToolsValues
from app.utils.graph_connection_manager import GraphConnectionManager
from gremlin_python.process.traversal import T

def sync_data_to_graph():
    client = GraphConnectionManager.get_client()
    
    # Clear existing graph data (optional)
    client.submit("g.V().drop()").all().result()

    # Sync Threat Actors
    all_groups = AllGroups.query.all()
    for group in all_groups:
        client.submit(
            "g.addV('ThreatActor').property('id', uuid).property('name', name)",
            {'uuid': str(group.uuid), 'name': group.name}
        ).all().result()
        # Add relationships and properties as needed

    # Sync Tools
    all_tools = AllTools.query.all()
    for tool in all_tools:
        client.submit(
            "g.addV('Tool').property('id', uuid).property('name', name)",
            {'uuid': str(tool.uuid), 'name': tool.name}
        ).all().result()
        # Add relationships and properties as needed

    # Create Relationships
    # Implement logic to create edges between nodes based on relationships

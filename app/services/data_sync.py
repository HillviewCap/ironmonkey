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

        # Add associated Tools
        for value in group.values:
            if value.tools:
                for tool_name in value.tools.split(','):
                    tool_name = tool_name.strip()
                    # Add Tool nodes
                    client.submit(
                        "g.addV('Tool').property('name', name)",
                        {'name': tool_name}
                    ).all().result()
                    
                    # Create 'uses' edge between ThreatActor and Tool
                    client.submit(
                        "g.V().has('ThreatActor', 'name', actor_name)"
                        ".as('a')"
                        ".V().has('Tool', 'name', tool_name)"
                        ".addE('uses').from('a')",
                        {'actor_name': group.name, 'tool_name': tool_name}
                    ).all().result()

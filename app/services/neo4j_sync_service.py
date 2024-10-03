from app.utils.graph_connection_manager import GraphConnectionManager
from app.models.relational.parsed_content import ParsedContent
from flask import current_app

class Neo4jSyncService:
    @staticmethod
    def sync_parsed_content_to_neo4j():
        driver = GraphConnectionManager.get_driver()
        if driver is None:
            current_app.logger.warning('Neo4j driver not initialized.')
            return

        contents = ParsedContent.query.all()
        with driver.session() as session:
            for content in contents:
                session.run(
                    """
                    MERGE (c:Content {id: $id})
                    SET c.title = $title, c.description = $description
                    """,
                    id=str(content.id),
                    title=content.title,
                    description=content.description
                )
                
                # Create ThreatActor node (assuming content.creator is the actor's name)
                if content.creator:
                    session.run(
                        """
                        MERGE (ta:ThreatActor {name: $actor_name})
                        """,
                        actor_name=content.creator
                    )
                    # Create relationship between ThreatActor and Content
                    session.run(
                        """
                        MATCH (c:Content {id: $content_id}), (ta:ThreatActor {name: $actor_name})
                        MERGE (ta)-[:ASSOCIATED_WITH]->(c)
                        """,
                        content_id=str(content.id),
                        actor_name=content.creator
                    )
                
                # Create Location node and relationship (assuming content.geography exists)
                if content.geography:
                    session.run(
                        """
                        MERGE (loc:Location {name: $location})
                        """,
                        location=content.geography
                    )
                    # Associate ThreatActor with Location
                    if content.creator:
                        session.run(
                            """
                            MATCH (ta:ThreatActor {name: $actor_name}), (loc:Location {name: $location})
                            MERGE (ta)-[:OPERATES_IN]->(loc)
                            """,
                            actor_name=content.creator,
                            location=content.geography
                        )
                
                # Create Tool nodes and relationships (assuming content.tools_used is a list)
                if content.tools_used:
                    for tool_name in content.tools_used:
                        session.run(
                            """
                            MERGE (t:Tool {name: $tool_name})
                            """,
                            tool_name=tool_name
                        )
                        # Associate ThreatActor with Tool
                        if content.creator:
                            session.run(
                                """
                                MATCH (ta:ThreatActor {name: $actor_name}), (t:Tool {name: $tool_name})
                                MERGE (ta)-[:USES_TOOL]->(t)
                                """,
                                actor_name=content.creator,
                                tool_name=tool_name
                            )

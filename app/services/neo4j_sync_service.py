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

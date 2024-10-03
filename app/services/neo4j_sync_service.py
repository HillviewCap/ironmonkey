from app.utils.graph_connection_manager import GraphConnectionManager
from app.models.relational.allgroups import AllGroups, AllGroupsValues, AllGroupsValuesNames
from app.models.relational.alltools import AllTools, AllToolsValues, AllToolsValuesNames
from app.models.relational.parsed_content import ParsedContent
from app.utils.logging_config import setup_logger

# Initialize logger for Neo4jSyncService
logger = setup_logger('neo4j_sync_service', 'neo4j_sync_service.log')

class Neo4jSyncService:
    @staticmethod
    def sync_parsed_content_to_neo4j():
        logger.info('Starting sync of ParsedContent to Neo4j.')
        driver = GraphConnectionManager.get_driver()
        driver = GraphConnectionManager.get_driver()
        if driver is None:
            return

        # Fetch all ParsedContent records
        parsed_contents = ParsedContent.query.all()
        if not parsed_contents:
            logger.info('No ParsedContent records found to sync.')
            return

        with driver.session() as session:
            for content in parsed_contents:
                logger.debug(f'Processing ParsedContent: {content.title} (ID: {content.id})')
                try:
                    # Create ParsedContent node with UUID
                    session.run(
                        """
                        MERGE (pc:ParsedContent {id: $id})
                        SET pc.title = $title,
                            pc.creator = $creator,
                            pc.pub_date = $pub_date,
                            pc.category = $category,
                            pc.summary = $summary,
                            pc.link = $link,
                            pc.image_link = $image_link,
                            pc.parsed_date = $parsed_date,
                            pc.feed_title = $feed_title
                        """,
                        id=str(content.id),
                        title=content.title,
                        creator=content.creator,
                        pub_date=content.pub_date if content.pub_date else None,
                        category=content.category,
                        summary=content.summary,
                        link=content.link,
                        image_link=content.image_link,
                        parsed_date=content.parsed_date.strftime('%Y-%m-%d %H:%M:%S') if content.parsed_date else None,
                        feed_title=content.rss_feed.title if content.rss_feed else None
                    )
                    logger.debug(f'Synced ParsedContent node for {content.title}')
                except Exception as e:
                    logger.error(f'Error syncing ParsedContent {content.id}: {e}')

        logger.info('Completed sync of ParsedContent to Neo4j.')

    @staticmethod
    def sync_allgroups_to_neo4j():
        driver = GraphConnectionManager.get_driver()
        if driver is None:
            logger.warning('Neo4j driver not initialized.')
            return

        logger.info('Starting sync of AllGroups to Neo4j.')
        all_groups = AllGroups.query.all()
        with driver.session() as session:
            for group in all_groups:
                logger.debug(f'Processing group: {group.name} (UUID: {group.uuid})')
                # Create Group node with UUID
                session.run(
                    """
                    MERGE (g:Group {uuid: $uuid})
                    SET g.name = $name,
                        g.category = $category,
                        g.type = $type,
                        g.description = $description,
                        g.tlp = $tlp,
                        g.last_db_change = $last_db_change
                    """,
                    uuid=str(group.uuid),
                    name=group.name,
                    category=group.category,
                    type=group.type,
                    description=group.description,
                    tlp=group.tlp,
                    last_db_change=group.last_db_change
                )
                # Process associated values
                for value in group.values:
                    # Create GroupValue node with UUID
                    session.run(
                        """
                        MERGE (gv:GroupValue {uuid: $uuid})
                        SET gv.actor = $actor,
                            gv.country = $country,
                            gv.description = $description,
                            gv.information = $information,
                            gv.last_card_change = $last_card_change,
                            gv.motivation = $motivation,
                            gv.first_seen = $first_seen,
                            gv.observed_sectors = $observed_sectors,
                            gv.observed_countries = $observed_countries,
                            gv.operations = $operations,
                            gv.sponsor = $sponsor,
                            gv.counter_operations = $counter_operations,
                            gv.mitre_attack = $mitre_attack,
                            gv.playbook = $playbook
                        """,
                        uuid=str(value.uuid),
                        actor=value.actor,
                        country=value.country,
                        description=value.description,
                        information=value.information,
                        last_card_change=value.last_card_change,
                        motivation=value.motivation,
                        first_seen=value.first_seen,
                        observed_sectors=value.observed_sectors,
                        observed_countries=value.observed_countries,
                        operations=value.operations,
                        sponsor=value.sponsor,
                        counter_operations=value.counter_operations,
                        mitre_attack=value.mitre_attack,
                        playbook=value.playbook
                    )

                    # Create relationship between Group and GroupValue
                    session.run(
                        """
                        MATCH (g:Group {uuid: $group_uuid}), (gv:GroupValue {uuid: $value_uuid})
                        MERGE (g)-[:HAS_VALUE]->(gv)
                        """,
                        group_uuid=str(group.uuid),
                        value_uuid=str(value.uuid)
                    )

                    # Process associated names
                    for name in value.names:
                        # Create GroupName node with UUID
                        session.run(
                            """
                            MERGE (n:GroupName {uuid: $uuid})
                            SET n.name = $name,
                                n.name_giver = $name_giver
                            """,
                            uuid=str(name.uuid),
                            name=name.name,
                            name_giver=name.name_giver
                        )

                        # Create relationship between GroupValue and GroupName
                        session.run(
                            """
                            MATCH (gv:GroupValue {uuid: $value_uuid}), (n:GroupName {uuid: $name_uuid})
                            MERGE (gv)-[:HAS_NAME]->(n)
                            """,
                            value_uuid=str(value.uuid),
                            name_uuid=str(name.uuid)
                        )

    @staticmethod
    def sync_alltools_to_neo4j():
        driver = GraphConnectionManager.get_driver()
        if driver is None:
            logger.warning('Neo4j driver not initialized.')
            return

        logger.info('Starting sync of AllTools to Neo4j.')
        all_tools = AllTools.query.all()
        with driver.session() as session:
            for tool in all_tools:
                logger.debug(f'Processing tool: {tool.name} (UUID: {tool.uuid})')
                # Create Tool node with UUID
                session.run(
                    """
                    MERGE (t:Tool {uuid: $uuid})
                    SET t.name = $name,
                        t.category = $category,
                        t.type = $type,
                        t.description = $description,
                        t.tlp = $tlp,
                        t.last_db_change = $last_db_change
                    """,
                    uuid=str(tool.uuid),
                    name=tool.name,
                    category=tool.category,
                    type=tool.type,
                    description=tool.description,
                    tlp=tool.tlp,
                    last_db_change=tool.last_db_change
                )
                # Process associated values
                for value in tool.values:
                    # Create ToolValue node with UUID
                    session.run(
                        """
                        MERGE (tv:ToolValue {uuid: $uuid})
                        SET tv.tool = $tool_name,
                            tv.description = $description,
                            tv.category = $category,
                            tv.type = $type,
                            tv.information = $information,
                            tv.last_card_change = $last_card_change
                        """,
                        uuid=str(value.uuid),
                        tool_name=value.tool,
                        description=value.description,
                        category=value.category,
                        type=value.type,
                        information=value.information,
                        last_card_change=value.last_card_change
                    )

                    # Create relationship between Tool and ToolValue
                    session.run(
                        """
                        MATCH (t:Tool {uuid: $tool_uuid}), (tv:ToolValue {uuid: $value_uuid})
                        MERGE (t)-[:HAS_VALUE]->(tv)
                        """,
                        tool_uuid=str(tool.uuid),
                        value_uuid=str(value.uuid)
                    )

                    # Process associated names
                    for name in value.names:
                        # Create ToolName node with UUID
                        session.run(
                            """
                            MERGE (n:ToolName {uuid: $uuid})
                            SET n.name = $name
                            """,
                            uuid=str(name.uuid),
                            name=name.name
                        )

                        # Create relationship between ToolValue and ToolName
                        session.run(
                            """
                            MATCH (tv:ToolValue {uuid: $value_uuid}), (n:ToolName {uuid: $name_uuid})
                            MERGE (tv)-[:HAS_NAME]->(n)
                            """,
                            value_uuid=str(value.uuid),
                            name_uuid=str(name.uuid)
                        )
    logger.info('Completed sync of AllTools to Neo4j.')

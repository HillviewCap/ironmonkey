from app.utils.graph_connection_manager import GraphConnectionManager
from app.models.relational.allgroups import AllGroups, AllGroupsValues, AllGroupsValuesNames
from app.models.relational.alltools import AllTools, AllToolsValues, AllToolsValuesNames
from app.models.relational.parsed_content import ParsedContent
from sqlalchemy.orm import joinedload
from app.utils.logging_config import setup_logger
from neo4j import exceptions
import logging
from tqdm import tqdm

# Initialize logger for Neo4jSyncService
logger = setup_logger('neo4j_sync_service', 'neo4j_sync_service.log', level=logging.INFO)

class Neo4jSyncService:
    @staticmethod
    def create_uniqueness_constraints():
        driver = GraphConnectionManager.get_driver()
        if driver is None:
            logger.warning('Neo4j driver not initialized.')
            return

        with driver.session() as session:
            # ParsedContent node constraint
            session.run("CREATE CONSTRAINT parsedContentId IF NOT EXISTS FOR (pc:ParsedContent) REQUIRE pc.id IS UNIQUE")
            # Category node constraint
            session.run("CREATE CONSTRAINT categoryName IF NOT EXISTS FOR (c:Category) REQUIRE c.name IS UNIQUE")
            # Add uniqueness constraints for new nodes
            session.run("CREATE CONSTRAINT threatActorUuid IF NOT EXISTS FOR (ta:ThreatActor) REQUIRE ta.uuid IS UNIQUE")
            session.run("CREATE CONSTRAINT toolUuid IF NOT EXISTS FOR (t:Tool) REQUIRE t.uuid IS UNIQUE")
            session.run("CREATE CONSTRAINT sectorName IF NOT EXISTS FOR (s:Sector) REQUIRE s.name IS UNIQUE")
            session.run("CREATE CONSTRAINT countryName IF NOT EXISTS FOR (c:Country) REQUIRE c.name IS UNIQUE")
        logger.info('Starting sync of ParsedContent to Neo4j.')
        driver = GraphConnectionManager.get_driver()
        if driver is None:
            return

        # Fetch all ParsedContent records
        parsed_contents = ParsedContent.query.all()
        if not parsed_contents:
            logger.info('No ParsedContent records found to sync.')
            return

        logger.info(f'Fetched {len(parsed_contents)} parsed content records to sync.')

        with driver.session() as session:
            with session.begin_transaction() as tx:
                for content in tqdm(parsed_contents, desc="Syncing ParsedContent"):
                    try:
                        # Create ParsedContent node with UUID
                        tx.run(
                            """
                            MERGE (pc:ParsedContent {id: $id})
                            SET pc.title = $title,
                                pc.creator = $creator,
                                pc.pub_date = $pub_date,
                                pc.summary = $summary,
                                pc.url = $url,
                                pc.created_at = $created_at,
                                pc.feed_title = $feed_title
                            """,
                            id=str(content.id),
                            title=content.title,
                            creator=content.creator,
                            pub_date=content.pub_date if content.pub_date else None,
                            summary=content.summary,
                            url=content.url,
                            created_at=content.created_at.strftime('%Y-%m-%d %H:%M:%S') if content.created_at else None,
                            feed_title=content.feed.title if content.feed else None
                        )
                        # Sync categories associated with ParsedContent
                        for category in content.categories:
                            tx.run(
                                """
                                MERGE (c:Category {name: $category_name})
                                WITH c
                                MATCH (pc:ParsedContent {id: $id})
                                MERGE (pc)-[r:HAS_CATEGORY]->(c)
                                """,
                                category_name=category.name,
                                id=str(content.id)
                            )
                    except exceptions.ServiceUnavailable as e:
                        logger.exception(f'Neo4j service unavailable: {e}')
                        logger.error(f'Error syncing ParsedContent {content.id}: {e}')

        logger.info('Completed sync of ParsedContent to Neo4j.')

    @staticmethod
    def sync_threat_actors_to_neo4j():
        driver = GraphConnectionManager.get_driver()
        if driver is None:
            logger.warning('Neo4j driver not initialized.')
            return

        logger.info('Starting sync of ThreatActors to Neo4j.')

        # Fetch ThreatActor records from the relational database
        threat_actors = AllGroupsValues.query.all()
        if not threat_actors:
            logger.info('No ThreatActor records found to sync.')
            return

        with driver.session() as session:
            for actor in tqdm(threat_actors, desc="Syncing ThreatActors"):
                try:
                    # Create or update ThreatActor node
                    session.run(
                        """
                        MERGE (ta:ThreatActor {uuid: $uuid})
                        SET ta.actor = $actor,
                            ta.country = $country,
                            ta.description = $description,
                            ta.motivation = $motivation,
                            ta.first_seen = $first_seen,
                            ta.observed_sectors = $observed_sectors,
                            ta.observed_countries = $observed_countries,
                            ta.operations = $operations,
                            ta.sponsor = $sponsor,
                            ta.counter_operations = $counter_operations,
                            ta.mitre_attack = $mitre_attack,
                            ta.playbook = $playbook
                        """,
                        uuid=str(actor.uuid),
                        actor=actor.actor,
                        country=actor.country,
                        description=actor.description,
                        motivation=actor.motivation,
                        first_seen=actor.first_seen,
                        observed_sectors=actor.observed_sectors,
                        observed_countries=actor.observed_countries,
                        operations=actor.operations,
                        sponsor=actor.sponsor,
                        counter_operations=actor.counter_operations,
                        mitre_attack=actor.mitre_attack,
                        playbook=actor.playbook
                    )

                    # Create ORIGINATES_FROM relationship with Country
                    if actor.country:
                        session.run(
                            """
                            MERGE (c:Country {name: $country_name})
                            MERGE (ta:ThreatActor {uuid: $uuid})
                            MERGE (ta)-[:ORIGINATES_FROM]->(c)
                            """,
                            country_name=actor.country,
                            uuid=str(actor.uuid)
                        )

                    # Create TARGETS_SECTOR relationships
                    if actor.observed_sectors:
                        sectors = actor.observed_sectors.split(', ')
                        for sector_name in sectors:
                            session.run(
                                """
                                MERGE (s:Sector {name: $sector_name})
                                MERGE (ta:ThreatActor {uuid: $uuid})
                                MERGE (ta)-[:TARGETS_SECTOR]->(s)
                                """,
                                sector_name=sector_name.strip(),
                                uuid=str(actor.uuid)
                            )

                    # Create TARGETS_COUNTRY relationships
                    if actor.observed_countries:
                        countries = actor.observed_countries.split(', ')
                        for country_name in countries:
                            session.run(
                                """
                                MERGE (c:Country {name: $country_name})
                                MERGE (ta:ThreatActor {uuid: $uuid})
                                MERGE (ta)-[:TARGETS_COUNTRY]->(c)
                                """,
                                country_name=country_name.strip(),
                                uuid=str(actor.uuid)
                            )
                except Exception as e:
                    logger.error(f'Error syncing ThreatActor {actor.uuid}: {e}')

        logger.info('Completed sync of ThreatActors to Neo4j.')

    @staticmethod
    def sync_alltools_to_neo4j():
        driver = GraphConnectionManager.get_driver()
        if driver is None:
            logger.warning('Neo4j driver not initialized.')
            return

        logger.info('Starting sync of Tools to Neo4j.')
        all_tools_values = AllToolsValues.query.all()
        with driver.session() as session:
            for tool in tqdm(all_tools_values, desc="Syncing Tools"):
                try:
                    # Create or update Tool node
                    session.run(
                        """
                        MERGE (t:Tool {uuid: $uuid})
                        SET t.tool = $tool_name,
                            t.description = $description,
                            t.category = $category,
                            t.type = $type,
                            t.information = $information,
                            t.last_card_change = $last_card_change
                        """,
                        uuid=str(tool.uuid),
                        tool_name=tool.tool,
                        description=tool.description,
                        category=tool.category,
                        type=tool.type,
                        information=tool.information,
                        last_card_change=tool.last_card_change
                    )

                    # Establish USES relationships
                    # Assuming there's a relationship in the database between tools and threat actors
                    if tool.threat_actors:
                        for actor in tool.threat_actors:
                            session.run(
                                """
                                MATCH (ta:ThreatActor {uuid: $actor_uuid})
                                MATCH (t:Tool {uuid: $tool_uuid})
                                MERGE (ta)-[:USES]->(t)
                                """,
                                actor_uuid=str(actor.uuid),
                                tool_uuid=str(tool.uuid)
                            )
                except Exception as e:
                    logger.error(f'Error syncing Tool {tool.uuid}: {e}')
        logger.info('Completed sync of Tools to Neo4j.')

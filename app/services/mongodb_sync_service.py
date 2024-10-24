import os
from pymongo import MongoClient
from app.models.relational.parsed_content import ParsedContent
from app.utils.db_connection_manager import DBConnectionManager
from logging import getLogger
from app.models.relational.allgroups import AllGroups, AllGroupsValues, AllGroupsValuesNames
from sqlalchemy.orm import joinedload
from app.models.relational.alltools import AllTools
from flask import current_app

logger = getLogger(__name__)

class MongoDBSyncService:
    @staticmethod
    def get_mongo_client():
        with current_app.app_context():
            mongodb_uri = current_app.config['MONGODB_URI']
        return MongoClient(mongodb_uri)

    @staticmethod
    def sync_parsed_content_to_mongodb():
        """Synchronize parsed_content table to MongoDB."""
        mongo_client = None
        try:
            mongo_client = MongoDBSyncService.get_mongo_client()
            mongo_db = mongo_client[current_app.config['MONGO_DB_NAME']]
            mongo_collection = mongo_db['parsed_content']
            sync_meta_collection = mongo_db['sync_metadata']

            # Initialize last_sync_time to None
            last_sync_time = None

            # Load last sync time from MongoDB
            sync_meta = sync_meta_collection.find_one({'_id': 'last_sync_time'})
            if sync_meta and 'timestamp' in sync_meta:
                last_sync_time = sync_meta['timestamp']

            # Access the parsed_content data
            with DBConnectionManager.get_session() as session:
                query = session.query(ParsedContent)
                if last_sync_time is not None:
                    query = query.filter(ParsedContent.created_at > last_sync_time)

                parsed_contents = query.all()

                # Prepare and upsert data
                for content in parsed_contents:
                    document = {
                        '_id': str(content.id),
                        'title': content.title,
                        'url': content.url,
                        'description': content.description,
                        'content': content.content,
                        'summary': content.summary,
                        'feed_id': str(content.feed_id),
                        'created_at': content.created_at,
                        'pub_date': content.pub_date,
                        'creator': content.creator,
                        'art_hash': content.art_hash,
                    }

                    # Upsert the document into MongoDB
                    mongo_collection.update_one(
                        {'_id': document['_id']},
                        {'$set': document},
                        upsert=True
                    )

                # Update last sync time in MongoDB
                if parsed_contents:
                    last_synced_time = parsed_contents[-1].created_at
                    sync_meta_collection.update_one(
                        {'_id': 'last_sync_time'},
                        {'$set': {'timestamp': last_synced_time}},
                        upsert=True
                    )
                    logger.info(f"Incrementally synced {len(parsed_contents)} parsed_content records to MongoDB.")
                else:
                    logger.info("No new records to sync.")

        except Exception as e:
            logger.error(f"Error syncing parsed_content to MongoDB: {str(e)}")
        finally:
            if mongo_client:
                mongo_client.close()
    @staticmethod
    def sync_alltools_to_mongodb():
        """Synchronize alltools table to MongoDB, creating a separate document for each tool."""
        mongo_client = None
        try:
            mongo_client = MongoDBSyncService.get_mongo_client()
            mongo_db = mongo_client[current_app.config['MONGO_DB_NAME']]
            mongo_collection = mongo_db['alltools']
            sync_meta_collection = mongo_db['sync_metadata']

            # Load last sync time from MongoDB
            last_sync_time = sync_meta_collection.find_one({'_id': 'last_alltools_sync_time'})
            last_sync_time = last_sync_time['timestamp'] if last_sync_time else None
            logger.info(f"Last alltools sync time: {last_sync_time}")

            with DBConnectionManager.get_session() as session:
                query = session.query(AllTools).options(
                    joinedload(AllTools.values)
                )
                if last_sync_time:
                    query = query.filter(AllTools.last_db_change > last_sync_time)

                alltools = query.all()
                logger.info(f"Found {len(alltools)} alltools to sync")

                synced_tools_count = 0
                for tool in alltools:
                    for value in tool.values:
                        document = {
                            '_id': str(value.uuid),
                            'tool_uuid': str(tool.uuid),
                            'name': value.tool,
                            'description': value.description,
                            'category': value.category,
                            'type': value.type,
                            'information': value.information,
                            'last_card_change': value.last_card_change,
                            'authors': tool.authors,
                            'source': tool.source,
                            'tlp': tool.tlp,
                            'license': tool.license,
                            'last_db_change': tool.last_db_change
                        }

                        # Insert or update the document for this tool
                        result = mongo_collection.update_one(
                            {'_id': document['_id']},
                            {'$set': document},
                            upsert=True
                        )
                        logger.debug(f"Updated tool {value.tool}: matched={result.matched_count}, modified={result.modified_count}, upserted={result.upserted_id}")
                        synced_tools_count += 1

                if alltools:
                    last_synced_time = max(tool.last_db_change for tool in alltools)
                    sync_meta_collection.update_one(
                        {'_id': 'last_alltools_sync_time'},
                        {'$set': {'timestamp': last_synced_time}},
                        upsert=True
                    )
                    logger.info(f"Incrementally synced {synced_tools_count} individual tools from {len(alltools)} alltools records to MongoDB. Last sync time updated to {last_synced_time}")
                else:
                    logger.info("No new alltools records to sync.")

        except Exception as e:
            logger.error(f"Error syncing alltools to MongoDB: {str(e)}", exc_info=True)
        finally:
            if mongo_client:
                mongo_client.close()

    @staticmethod
    def sync_allgroups_to_mongodb():
        """Synchronize allgroups, allgroups_values, and allgroups_values_names to MongoDB."""
        mongo_client = None
        try:
            mongo_client = MongoDBSyncService.get_mongo_client()
            mongo_db = mongo_client[current_app.config['MONGO_DB_NAME']]
            mongo_collection = mongo_db['allgroups']
            sync_meta_collection = mongo_db['sync_metadata']

            # Load last sync time from MongoDB
            last_sync_time = sync_meta_collection.find_one({'_id': 'last_allgroups_sync_time'})
            last_sync_time = last_sync_time['timestamp'] if last_sync_time else None

            with DBConnectionManager.get_session() as session:
                query = session.query(AllGroups).options(
                    joinedload(AllGroups.values).joinedload(AllGroupsValues.names)
                )
                if last_sync_time:
                    query = query.filter(AllGroups.last_db_change > last_sync_time)

                allgroups = query.all()

                for group in allgroups:
                    document = {
                        '_id': str(group.uuid),
                        'authors': group.authors,
                        'category': group.category,
                        'name': group.name,
                        'type': group.type,
                        'source': group.source,
                        'description': group.description,
                        'tlp': group.tlp,
                        'license': group.license,
                        'last_db_change': group.last_db_change,
                        'values': []
                    }

                    for value in group.values:
                        value_doc = {
                            'uuid': str(value.uuid),
                            'actor': value.actor,
                            'country': value.country,
                            'description': value.description,
                            'information': value.information,
                            'last_card_change': value.last_card_change,
                            'motivation': value.motivation,
                            'first_seen': value.first_seen,
                            'observed_sectors': value.observed_sectors,
                            'observed_countries': value.observed_countries,
                            'tools': value.tools,
                            'operations': value.operations,
                            'sponsor': value.sponsor,
                            'counter_operations': value.counter_operations,
                            'mitre_attack': value.mitre_attack,
                            'playbook': value.playbook,
                            'names': [
                                {
                                    'uuid': str(name.uuid),
                                    'name': name.name,
                                    'name_giver': name.name_giver
                                } for name in value.names
                            ]
                        }
                        document['values'].append(value_doc)

                    # Upsert the document into MongoDB
                    mongo_collection.update_one(
                        {'_id': document['_id']},
                        {'$set': document},
                        upsert=True
                    )

                if allgroups:
                    last_synced_time = max(group.last_db_change for group in allgroups)
                    sync_meta_collection.update_one(
                        {'_id': 'last_allgroups_sync_time'},
                        {'$set': {'timestamp': last_synced_time}},
                        upsert=True
                    )
                    logger.info(f"Incrementally synced {len(allgroups)} allgroups records to MongoDB.")
                else:
                    logger.info("No new allgroups records to sync.")

        except Exception as e:
            logger.error(f"Error syncing allgroups to MongoDB: {str(e)}")
        finally:
            if mongo_client:
                mongo_client.close()

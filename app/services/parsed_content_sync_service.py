import os
from pymongo import MongoClient
from app.models.relational.parsed_content import ParsedContent
from app.utils.db_connection_manager import DBConnectionManager
from logging import getLogger

logger = getLogger(__name__)

def sync_parsed_content_to_mongodb(app):
    """Synchronize parsed_content table to MongoDB."""
    with app.app_context():
        try:
            # Get MongoDB URI and database name from app config
            mongo_uri = app.config['MONGODB_URI']
            mongo_db_name = app.config['MONGO_DB_NAME']

            mongo_collection = mongo_db['parsed_content']

            # Define a collection for sync metadata
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
            # Close the MongoDB connection
            mongo_client.close()

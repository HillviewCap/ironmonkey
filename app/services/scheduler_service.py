import asyncio
import os
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from app.models.relational import ParsedContent, RSSFeed
from app.services.feed_parser_service import fetch_and_parse_feed_sync
from app.services.summary_service import SummaryService
from app.services.news_rollup_service import NewsRollupService
from flask import current_app
from app.utils.db_connection_manager import DBConnectionManager
from logging import getLogger
from app.utils.auto_tagger import tag_untagged_content
from app.utils.threat_group_cards_updater import update_threat_group_cards
from pymongo import MongoClient
from app.models.relational.parsed_content import ParsedContent
import json

logger = getLogger(__name__)
scheduler_logger = getLogger("scheduler")


class SchedulerService:
    _instance = None

    def __new__(cls, app):
        if cls._instance is None:
            cls._instance = super(SchedulerService, cls).__new__(cls)
            cls._instance.app = app
            executors = {
                'default': ThreadPoolExecutor(max_workers=5)  # Adjust max_workers as needed
            }
            cls._instance.scheduler = BackgroundScheduler(executors=executors)
            cls._instance.is_running = False
        return cls._instance

    def setup_scheduler(self):
        if self.is_running:
            logger.warning("Scheduler is already running. Skipping setup.")
            return

        rss_check_interval = int(os.getenv("RSS_CHECK_INTERVAL", 30))
        summary_check_interval = int(os.getenv("SUMMARY_CHECK_INTERVAL", 31))
        auto_tag_interval = int(os.getenv("AUTO_TAG_INTERVAL", 60))  # Default to 60 minutes if not set

        self.scheduler.add_job(
            func=self.check_and_process_rss_feeds,
            trigger="interval",
            minutes=rss_check_interval,
        )

        summary_api_choice = os.getenv("SUMMARY_API_CHOICE", "ollama").lower()
        if summary_api_choice == "ollama":
            self.scheduler.add_job(
                func=self.start_check_empty_summaries,
                trigger="interval",
                minutes=summary_check_interval,
            )
            logger.info(
                f"Scheduler configured with Ollama API for summaries, check interval: {summary_check_interval} minutes"
            )
        elif summary_api_choice == "groq":
            # Add Groq-specific job here if needed
            logger.info(
                "Scheduler configured with Groq API for summaries, no automatic summary generation scheduled"
            )
        else:
            logger.warning(
                f"Invalid SUMMARY_API_CHOICE: {summary_api_choice}. No summary generation scheduled."
            )

        # Add jobs for creating rollups
        self.scheduler.add_job(
            func=self.create_morning_rollup,
            trigger="cron",
            hour=6,
            minute=0
        )
        self.scheduler.add_job(
            func=self.create_midday_rollup,
            trigger="cron",
            hour=12,
            minute=0
        )
        self.scheduler.add_job(
            func=self.create_end_of_day_rollup,
            trigger="cron",
            hour=16,
            minute=0
        )

        # Add the new auto-tagging job
        self.scheduler.add_job(
            func=self.auto_tag_untagged_content,
            trigger="interval",
            minutes=auto_tag_interval,
        )
        logger.info(f"Scheduled auto-tagging job to run every {auto_tag_interval} minutes")

        # Schedule the update_threat_group_cards function to run every 12 hours
        self.scheduler.add_job(
            func=self.update_threat_group_cards_job,
            trigger='interval',
            hours=12,  # Adjust the interval as required
            id='update_threat_group_cards_job',
            replace_existing=True
        )
        logger.info("Scheduled job added: update_threat_group_cards_job")

        # Define the synchronization interval in minutes (default to 60 if not set)
        sync_interval = int(os.getenv("PARSED_CONTENT_SYNC_INTERVAL", 60))

        # Schedule the sync_parsed_content_to_mongodb job
        self.scheduler.add_job(
            func=self.sync_parsed_content_to_mongodb,
            trigger="interval",
            minutes=sync_interval,
            id='sync_parsed_content_to_mongodb',
            replace_existing=True
        )

        logger.info(f"Scheduled job 'sync_parsed_content_to_mongodb' to run every {sync_interval} minutes.")
        self.scheduler.start()
        self.is_running = True
        logger.info(
            f"Scheduler started successfully with RSS check interval: {rss_check_interval} minutes"
        )

    def sync_parsed_content_to_mongodb(self):
        """Synchronize parsed_content table to MongoDB."""
        with self.app.app_context():
            try:
                # Retrieve MongoDB credentials from environment variables
                mongo_username = os.getenv('MONGO_USERNAME', 'ironmonkey')
                mongo_password = os.getenv('MONGO_PASSWORD', 'the')
                mongo_host = os.getenv('MONGO_HOST', 'localhost')
                mongo_port = os.getenv('MONGO_PORT', '27017')
                mongo_db_name = os.getenv('MONGO_DB_NAME', 'threats_db')

                # Construct the MongoDB URI
                mongo_uri = f"mongodb://{mongo_username}:{mongo_password}@{mongo_host}:{mongo_port}/"

                # Establish connection to MongoDB
                mongo_client = MongoClient(mongo_uri)
                mongo_db = mongo_client[mongo_db_name]
                mongo_collection = mongo_db['parsed_content']

                # Define a collection for sync metadata
                sync_meta_collection = mongo_db['sync_metadata']

                # Load last sync time from MongoDB
                sync_meta = sync_meta_collection.find_one({'_id': 'last_sync_time'})
                if sync_meta and 'timestamp' in sync_meta:
                    last_sync_time = sync_meta['timestamp']

                # Access the parsed_content data
                with DBConnectionManager.get_session() as session:
                    query = session.query(ParsedContent)
                    if last_sync_time:
                        query = query.filter(ParsedContent.updated_at > last_sync_time)

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
                            'updated_at': content.updated_at,
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
                    sync_meta_collection.update_one(
                        {'_id': 'last_sync_time'},
                        {'$set': {'timestamp': datetime.utcnow()}},
                        upsert=True
                    )

                    logger.info(f"Incrementally synced {len(parsed_contents)} parsed_content records to MongoDB.")

            except Exception as e:
                logger.error(f"Error syncing parsed_content to MongoDB: {str(e)}")
            finally:
                # Close the MongoDB connection
                mongo_client.close()

    def check_and_process_rss_feeds(self):
        with self.app.app_context():
            with DBConnectionManager.get_session() as session:
                total_feeds = session.query(RSSFeed).count()
                new_articles_count = 0
                processed_feeds = 0

                scheduler_logger.info(f"Starting to process {total_feeds} RSS feeds")

                feed_ids = [feed.id for feed in session.query(RSSFeed).all()]

                for feed_id in feed_ids:
                    try:
                        feed = session.query(RSSFeed).get(feed_id)
                        if feed:
                            scheduler_logger.info(f"Processing feed: {feed.url}")
                            new_articles = fetch_and_parse_feed_sync(feed_id)
                            if new_articles is not None:
                                new_articles_count += new_articles
                                # Query for the feed again to ensure we have an attached instance
                                feed = session.query(RSSFeed).get(feed_id)
                                if feed:
                                    scheduler_logger.info(
                                        f"Added {new_articles} new articles from feed: {feed.url}"
                                    )
                                else:
                                    scheduler_logger.warning(
                                        f"Feed with id {feed_id} not found after processing"
                                    )
                            else:
                                scheduler_logger.warning(
                                    f"fetch_and_parse_feed returned None for feed {feed.url}"
                                )
                            processed_feeds += 1
                            scheduler_logger.info(
                                f"Processed {processed_feeds}/{total_feeds} feeds"
                            )
                        else:
                            scheduler_logger.warning(
                                f"Feed with id {feed_id} not found"
                            )
                    except Exception as e:
                        scheduler_logger.error(
                            f"Error processing feed {feed_id}: {str(e)}", exc_info=True
                        )

                    session.commit()

                scheduler_logger.info(
                    f"Finished processing {processed_feeds}/{total_feeds} RSS feeds, added {new_articles_count} new articles"
                )
        asyncio.run(self._start_check_empty_summaries_async())

    def start_check_empty_summaries(self):
        asyncio.run(self._start_check_empty_summaries_async())

    async def _start_check_empty_summaries_async(self):
        with self.app.app_context():
            processed_count = 0
            summary_service = SummaryService()

            with DBConnectionManager.get_session() as session:
                empty_summary_ids = (
                    session.query(ParsedContent.id)
                    .filter(ParsedContent.summary.is_(None))
                    .limit(50)
                    .all()
                )

            for (content_id,) in empty_summary_ids:
                try:
                    with DBConnectionManager.get_session() as session:
                        content = session.query(ParsedContent).get(content_id)
                        if content:
                            success = await summary_service.enhance_summary(content.id.hex)
                            if success:
                                processed_count += 1
                            else:
                                scheduler_logger.warning(
                                    f"Failed to generate summary for content {content.id}"
                                )
                        else:
                            scheduler_logger.warning(
                                f"Content with id {content_id} not found"
                            )
                except Exception as e:
                    scheduler_logger.error(
                        f"Error generating summary for content {content_id}: {str(e)}"
                    )

            scheduler_logger.info(
                f"Processed {processed_count} out of {len(empty_summary_ids)} empty summaries"
            )

    def create_morning_rollup(self):
        with self.app.app_context():
            try:
                asyncio.run(NewsRollupService().create_and_store_rollup("morning"))
                logger.info("Morning rollup created successfully")
            except Exception as e:
                logger.error(f"Error creating morning rollup: {str(e)}")

    def create_midday_rollup(self):
        with self.app.app_context():
            try:
                asyncio.run(NewsRollupService().create_and_store_rollup("midday"))
                logger.info("Midday rollup created successfully")
            except Exception as e:
                logger.error(f"Error creating midday rollup: {str(e)}")

    def create_end_of_day_rollup(self):
        with self.app.app_context():
            try:
                asyncio.run(NewsRollupService().create_and_store_rollup("end_of_day"))
                logger.info("End of day rollup created successfully")
            except Exception as e:
                logger.error(f"Error creating end of day rollup: {str(e)}")

    def auto_tag_untagged_content(self):
        with self.app.app_context():
            tag_untagged_content()

    def update_threat_group_cards_job(self):
        with self.app.app_context():
            update_threat_group_cards()
            logger.info("Scheduled job executed: Threat Group Cards JSON files updated.")

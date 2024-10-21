import asyncio
import os
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from app.models.relational import ParsedContent, RSSFeed
from app.services.feed_parser_service import fetch_and_parse_feed_sync
from app.services.summary_service import SummaryService
from app.services.news_rollup_service import NewsRollupService
from app.services.mongodb_sync_service import MongoDBSyncService
from flask import current_app
from app.utils.db_connection_manager import DBConnectionManager
from logging import getLogger
from app.utils.auto_tagger import tag_untagged_content
from app.utils.threat_group_cards_updater import update_threat_group_cards
from app.models.relational.parsed_content import ParsedContent

logger = getLogger(__name__)
scheduler_logger = getLogger("scheduler")


class SchedulerService:
    def __init__(self, app):
        self.app = app
        self.config = app.config
        executors = {
            'default': ThreadPoolExecutor(max_workers=10)  # Adjust max_workers as needed
        }
        self.scheduler = BackgroundScheduler(executors=executors)
        self.is_running = False

    def job_with_app_context(self, func):
        def wrapper(*args, **kwargs):
            with self.app.app_context():
                return func(*args, **kwargs)
        return wrapper

    def setup_scheduler(self):
        if self.is_running:
            logger.warning("Scheduler is already running. Skipping setup.")
            return

        config = self.app.config
        rss_check_interval = config['RSS_CHECK_INTERVAL']
        summary_check_interval = config['SUMMARY_CHECK_INTERVAL']
        summary_api_choice = config['SUMMARY_API_CHOICE'].lower()
        auto_tag_interval = config['AUTO_TAG_INTERVAL']
        sync_interval = config['PARSED_CONTENT_SYNC_INTERVAL']

        self.scheduler.add_job(
            func=self.job_with_app_context(self.check_and_process_rss_feeds),
            trigger="interval",
            minutes=rss_check_interval,
        )

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
            func=self.job_with_app_context(self.auto_tag_untagged_content),
            trigger="interval",
            minutes=auto_tag_interval,
        )
        logger.info(f"Scheduled auto-tagging job to run every {auto_tag_interval} minutes")

        # Schedule the update_threat_group_cards function to run every 12 hours
        self.scheduler.add_job(
            func=self.job_with_app_context(self.update_threat_group_cards_job),
            trigger='interval',
            hours=12,  # Adjust the interval as required
            id='update_threat_group_cards_job',
            replace_existing=True
        )
        logger.info("Scheduled job added: update_threat_group_cards_job")

        self.scheduler.add_job(
            func=self.job_with_app_context(MongoDBSyncService.sync_parsed_content_to_mongodb),
            trigger="interval",
            minutes=sync_interval,
            id='sync_parsed_content_to_mongodb',
            replace_existing=True
        )
        
        self.scheduler.add_job(
            func=self.job_with_app_context(MongoDBSyncService.sync_alltools_to_mongodb),
            trigger="interval",
            minutes=sync_interval,
            id='sync_alltools_to_mongodb',
            replace_existing=True
        )
        
        self.scheduler.add_job(
            func=self.job_with_app_context(MongoDBSyncService.sync_allgroups_to_mongodb),
            trigger="interval",
            minutes=sync_interval,
            id='sync_allgroups_to_mongodb',
            replace_existing=True
        )

        logger.info(f"Scheduled MongoDB sync jobs to run every {sync_interval} minutes.")
        self.scheduler.start()
        self.is_running = True
        logger.info(
            f"Scheduler started successfully with RSS check interval: {rss_check_interval} minutes"
        )


    def check_and_process_rss_feeds(self):
        with self.app.app_context():
            from app.models.relational.rss_feed import RSSFeed
            from app.services.feed_parser_service import fetch_and_parse_feed_sync
            
            with self.app.db.session() as session:
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
        with current_app.app_context():
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

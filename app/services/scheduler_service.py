import asyncio
import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from app.models.relational import ParsedContent, RSSFeed
from app.services.rss_feed_service import fetch_and_parse_feed
from app.services.summary_service import SummaryService
from flask import current_app
from app.utils.db_connection_manager import DBConnectionManager
from logging import getLogger

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

        if not self.is_running:
            self.scheduler.start()
            self.is_running = True
            logger.info(
                f"Scheduler started successfully with RSS check interval: {rss_check_interval} minutes"
            )
        else:
            logger.info("Scheduler was already running. Jobs updated.")

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

    async def start_check_empty_summaries(self):
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
                            success = summary_service.enhance_summary_sync(
                                str(content.id)
                            )
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

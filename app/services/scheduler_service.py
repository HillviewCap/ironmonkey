import asyncio
import os
from apscheduler.schedulers.background import BackgroundScheduler
from app.models.relational import ParsedContent, RSSFeed
from app.services.rss_feed_service import fetch_and_parse_feed
from app.services.summary_service import SummaryService
from flask import current_app
from app.utils.db_connection_manager import DBConnectionManager
from logging import getLogger

logger = getLogger(__name__)
scheduler_logger = getLogger('scheduler')

class SchedulerService:
    def __init__(self, app):
        self.app = app
        self.scheduler = BackgroundScheduler()

    def setup_scheduler(self):
        rss_check_interval = int(os.getenv("RSS_CHECK_INTERVAL", 30))
        summary_check_interval = int(os.getenv("SUMMARY_CHECK_INTERVAL", 31))

        self.scheduler.add_job(
            func=self.check_and_process_rss_feeds,
            trigger="interval",
            minutes=rss_check_interval
        )

        summary_api_choice = os.getenv("SUMMARY_API_CHOICE", "ollama").lower()
        if summary_api_choice == "ollama":
            self.scheduler.add_job(
                func=lambda: asyncio.run(self.start_check_empty_summaries()),
                trigger="interval",
                minutes=summary_check_interval,
            )
            logger.info(f"Scheduler started with Ollama API for summaries, check interval: {summary_check_interval} minutes")
        elif summary_api_choice == "groq":
            # Add Groq-specific job here if needed
            logger.info("Scheduler started with Groq API for summaries, no automatic summary generation scheduled")
        else:
            logger.warning(f"Invalid SUMMARY_API_CHOICE: {summary_api_choice}. No summary generation scheduled.")

        self.scheduler.start()
        logger.info(f"Scheduler started successfully with RSS check interval: {rss_check_interval} minutes")

    def check_and_process_rss_feeds(self):
        with self.app.app_context():
            with DBConnectionManager.get_session() as session:
                feeds = session.query(RSSFeed).all()
                new_articles_count = 0
                for feed in feeds:
                    try:
                        new_articles = asyncio.run(fetch_and_parse_feed(feed))
                        if new_articles is not None:
                            new_articles_count += new_articles
                        else:
                            scheduler_logger.warning(f"fetch_and_parse_feed returned None for feed {feed.url}")
                    except Exception as e:
                        scheduler_logger.error(f"Error processing feed {feed.url}: {str(e)}", exc_info=True)
                scheduler_logger.info(
                    f"Processed {len(feeds)} RSS feeds, added {new_articles_count} new articles"
                )

    async def start_check_empty_summaries(self):
        with self.app.app_context():
            with DBConnectionManager.get_session() as session:
                empty_summaries = (
                    session.query(ParsedContent)
                    .filter(ParsedContent.summary.is_(None))
                    .limit(10)
                    .all()
                )
                processed_count = 0
                summary_service = SummaryService()
                for content in empty_summaries:
                    try:
                        success = await summary_service.enhance_summary(str(content.id))
                        if success:
                            processed_count += 1
                        else:
                            scheduler_logger.warning(f"Failed to generate summary for content {content.id}")
                    except Exception as e:
                        scheduler_logger.error(
                            f"Error generating summary for content {content.id}: {str(e)}"
                        )
                scheduler_logger.info(
                    f"Processed {processed_count} out of {len(empty_summaries)} empty summaries"
                )

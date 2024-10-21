from app.extensions import db
import logging
from app.utils.ollama_client import OllamaAPI
from app.services.scheduler_service import SchedulerService
from app.services.apt_update_service import update_databases
from app.services.awesome_threat_intel_service import AwesomeThreatIntelService
from app.utils.threat_group_cards_updater import update_threat_group_cards

logger = logging.getLogger('app')

def initialize_services(app):
    with app.app_context():
        # Create all tables
        db.create_all()
        logger.info("All database tables created")
        app.ollama_api = OllamaAPI()

        # Setup scheduler
        app.scheduler = SchedulerService(app)
        app.scheduler.setup_scheduler()

        # Initialize Awesome Threat Intel Blogs
        AwesomeThreatIntelService.cleanup_awesome_threat_intel_blog_ids()
        AwesomeThreatIntelService.initialize_awesome_feeds()

        # Update APT databases
        update_databases()
        logger.info("APT databases updated at application startup")

        # Update the Threat Group Cards JSON files
        update_threat_group_cards()
        logger.info("Threat Group Cards JSON files updated at application startup")

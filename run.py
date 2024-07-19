import os
import logging
from dotenv import load_dotenv
from app import create_app
from app.extensions import db
from app.models.relational.user import User
from app.models.init_db import init_db

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = create_app()
logger.info("Application created")

with app.app_context():
    try:
        init_db(app)  # Initialize the database within the application context
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Error initializing the database: {e}")

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User}

def main():
    try:
        app.run(
            host='0.0.0.0',
            port=int(os.getenv('FLASK_PORT', 5000)),
            debug=os.getenv('FLASK_ENV') == 'development'
        )
        logger.info("Application started")
    except Exception as e:
        logger.error(f"Error starting the application: {e}")

if __name__ == '__main__':
    main()

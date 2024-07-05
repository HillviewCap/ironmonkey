import os
import logging
from dotenv import load_dotenv

load_dotenv()

import os
import logging
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))
instance_path = os.path.join(basedir, 'instance')

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', f'sqlite:///{os.path.join(instance_path, "threats.db")}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @staticmethod
    def init_app(app):
        # Ensure the directory for the database file exists
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        db_dir = os.path.dirname(db_path)
        if not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir, exist_ok=True)
                logging.getLogger(__name__).info(f"Created directory for database file at {db_dir}")
            except Exception as e:
                logging.getLogger(__name__).error(f"Error creating directory for database file: {str(e)}")
        else:
            logging.getLogger(__name__).info(f"Directory for database file already exists at {db_dir}")

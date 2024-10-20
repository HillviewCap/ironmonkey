import os
from pathlib import Path

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    BASE_DIR = Path(__file__).resolve().parent
    INSTANCE_PATH = os.getenv('INSTANCE_PATH', os.path.join(BASE_DIR, 'instance'))
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(INSTANCE_PATH, 'threats.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    RSS_CHECK_INTERVAL = int(os.getenv('RSS_CHECK_INTERVAL', 30))
    SUMMARY_CHECK_INTERVAL = int(os.getenv('SUMMARY_CHECK_INTERVAL', 60))
    SUMMARY_API_CHOICE = os.getenv('SUMMARY_API_CHOICE', 'groq')
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', '5000'))
    ELEVEN_API_KEY = os.getenv('ELEVEN_API_KEY')

class DevelopmentConfig(Config):
    DEBUG = True
    ENV = 'development'
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    DEBUG = False
    ENV = 'production'
    LOG_LEVEL = 'INFO'
    USE_RELOADER = False
    WAITRESS_HOST = os.getenv('WAITRESS_HOST', '0.0.0.0')
    WAITRESS_PORT = int(os.getenv('WAITRESS_PORT', '8080'))
    WAITRESS_THREADS = int(os.getenv('WAITRESS_THREADS', '4'))

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    LOG_LEVEL = 'DEBUG'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')
    return config.get(config_name, config['default'])

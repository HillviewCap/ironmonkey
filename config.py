import os
from pathlib import Path

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    INSTANCE_PATH = os.getenv('INSTANCE_PATH', 'instance')
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{Path(INSTANCE_PATH) / 'threats.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    RSS_CHECK_INTERVAL = int(os.getenv('RSS_CHECK_INTERVAL', 30))
    SUMMARY_CHECK_INTERVAL = int(os.getenv('SUMMARY_CHECK_INTERVAL', 60))
    SUMMARY_API_CHOICE = os.getenv('SUMMARY_API_CHOICE', 'groq')
    FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))

class DevelopmentConfig(Config):
    DEBUG = True
    FLASK_ENV = 'development'
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    DEBUG = False
    FLASK_ENV = 'production'
    LOG_LEVEL = 'INFO'

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

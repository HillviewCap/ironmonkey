import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(os.getenv('INSTANCE_PATH', 'instance'), 'threats.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    RSS_CHECK_INTERVAL = int(os.getenv('RSS_CHECK_INTERVAL', 30))
    SUMMARY_CHECK_INTERVAL = int(os.getenv('SUMMARY_CHECK_INTERVAL', 60))
    SUMMARY_API_CHOICE = os.getenv('SUMMARY_API_CHOICE', 'groq')

class DevelopmentConfig(Config):
    DEBUG = True
    FLASK_ENV = 'development'
    FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    DEBUG = False
    FLASK_ENV = 'production'
    FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))
    LOG_LEVEL = 'INFO'

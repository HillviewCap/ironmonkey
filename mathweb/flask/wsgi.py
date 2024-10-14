import os
from dotenv import load_dotenv
from app import create_app
from config import get_config

load_dotenv()

env = os.getenv("FLASK_ENV", "production")
config_obj = get_config(env)
app = create_app(config_obj)

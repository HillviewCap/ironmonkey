from flask import Blueprint

bp = Blueprint('user_settings', __name__)

from . import routes

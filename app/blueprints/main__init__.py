from flask import Blueprint

bp = Blueprint('main', __name__)

# Import routes at the bottom to avoid circular imports
from . import routes

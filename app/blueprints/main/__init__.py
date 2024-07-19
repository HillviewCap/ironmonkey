from flask import Blueprint

bp = Blueprint('main', __name__)

from . import routes  # Import routes at the end to avoid circular imports

# Explicitly export bp
__all__ = ['bp']

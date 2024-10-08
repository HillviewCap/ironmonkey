from flask import Blueprint

bp = Blueprint('main', __name__)

from . import routes

# Apply login_required to all routes in this blueprint
@bp.before_request
def before_request():
    pass

__all__ = ['bp']

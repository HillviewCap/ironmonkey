from flask import Blueprint
from flask_login import login_required

bp = Blueprint('main', __name__)

from . import routes

# Apply login_required to all routes in this blueprint
@bp.before_request
@login_required
def before_request():
    pass

__all__ = ['bp']

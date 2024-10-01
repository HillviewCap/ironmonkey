from flask import Blueprint
from flask_login import login_required

bp = Blueprint('parsed_content', __name__)

# Apply login_required to all routes in this blueprint
@bp.before_request
@login_required
def before_request():
    pass

from . import routes

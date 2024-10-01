from flask import Blueprint
from flask_login import login_required

bp = Blueprint('parsed_content', __name__)

# Import routes after creating the blueprint
from . import routes

# Apply login_required to all routes in this blueprint
for endpoint in bp.view_functions:
    bp.view_functions[endpoint] = login_required(bp.view_functions[endpoint])

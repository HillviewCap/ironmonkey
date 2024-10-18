from flask import Blueprint

dashboard_bp = Blueprint(
    'dashboard',
    __name__,
    template_folder='templates',
    static_folder='static'
)

from . import routes  # Import routes to register them with the blueprint

from flask import Blueprint

bp = Blueprint('main', __name__)

def init_app(app):
    app.register_blueprint(bp)
    
    # Import routes here to avoid circular imports
    from . import routes

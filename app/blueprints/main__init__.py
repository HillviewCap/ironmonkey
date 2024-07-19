from flask import Blueprint

bp = Blueprint('main', __name__)

def init_app(app):
    from . import routes
    app.register_blueprint(bp)

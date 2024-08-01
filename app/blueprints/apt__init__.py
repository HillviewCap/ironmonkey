from flask import Blueprint

apt = Blueprint('apt', __name__)

def init_app():
    from . import routes

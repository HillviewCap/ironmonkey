from flask import Blueprint

apt = Blueprint('apt', __name__)

from . import routes

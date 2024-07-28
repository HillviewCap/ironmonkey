from flask import Blueprint

bp = Blueprint('main', __name__)

from . import routes

__all__ = ['bp']

from flask import Blueprint, render_template, send_from_directory
import os
from app.models.relational.parsed_content import ParsedContent

main = Blueprint('main', __name__)

@main.route('/')
def index():
    recent_items = ParsedContent.query.order_by(ParsedContent.published.desc()).limit(6).all()
    return render_template('index.html', recent_items=recent_items)

@main.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(main.root_path, '..', '..', 'static', 'images'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

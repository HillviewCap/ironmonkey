from flask import Blueprint, render_template, send_from_directory, redirect, url_for, abort
from flask_login import current_user, login_required
import os
from app.models.relational.parsed_content import ParsedContent

main = Blueprint('main', __name__)

@main.route('/')
@login_required
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    recent_items = ParsedContent.query.order_by(ParsedContent.published.desc()).limit(6).all()
    return render_template('index.html', recent_items=recent_items)

@main.route('/item/<uuid:item_id>')
@login_required
def view_item(item_id):
    item = ParsedContent.query.get(item_id)
    if item is None:
        abort(404)
    return render_template('view_item.html', item=item)

@main.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(main.root_path, '..', '..', 'static', 'images'),
                               'favicon.ico', mimetype='image/x-icon')

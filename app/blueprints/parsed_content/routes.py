from flask import render_template, request, abort
from .services import ParsedContentService
from . import bp

@bp.route('/')
def parsed_content():
    category = request.args.get('category')
    latest_content = ParsedContentService.get_latest_parsed_content(category=category, limit=10)
    return render_template('parsed_content/index.html', content=latest_content['content'], stats=latest_content['stats'], selected_category=category)
from app.models.relational.parsed_content import ParsedContent

@bp.route('/item/<uuid:item_id>')
def view_item(item_id):
    item = ParsedContent.get_by_id(item_id)
    if not item:
        abort(404)
    return render_template('parsed_content/view_item.html', item=item)

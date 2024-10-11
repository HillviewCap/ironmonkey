from flask import Blueprint, render_template, jsonify
from app.models.relational.apt_group import APTGroup
from app.models.relational.apt_tool import APTTool

bp = Blueprint('apt', __name__)

@bp.route('/group/<string:group_id>')
def apt_group_detail(group_id):
    group = APTGroup.query.get_or_404(group_id)
    return render_template('apt-group-detail.html', group=group)

@bp.route('/tool/<string:tool_id>')
def apt_tool_detail(tool_id):
    tool = APTTool.query.get_or_404(tool_id)
    return render_template('apt-tools.html', tool=tool)

@bp.route('/api/entity/<string:entity_type>/<string:entity_id>')
def get_entity_details(entity_type, entity_id):
    if entity_type == 'APT_GROUP':
        entity = APTGroup.query.get_or_404(entity_id)
    elif entity_type == 'TOOL':
        entity = APTTool.query.get_or_404(entity_id)
    else:
        return jsonify({'error': 'Invalid entity type'}), 400

    return jsonify({
        'id': entity.id,
        'name': entity.name,
        'description': entity.description
    })

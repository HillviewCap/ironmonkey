from flask import Blueprint, render_template
from app.models.relational.allgroups import AllGroups

bp = Blueprint('apt', __name__)

@bp.route('/apt-groups')
def apt_groups():
    groups = AllGroups.query.all()
    return render_template('apt-groups.html', groups=groups)

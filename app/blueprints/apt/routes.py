from flask import render_template
from . import apt
from app.models.relational.allgroups import AllGroups

def init_routes():
    @apt.route('/apt-groups')
    def apt_groups():
        groups = AllGroups.query.all()
        return render_template('apt-groups.html', groups=groups)

init_routes()

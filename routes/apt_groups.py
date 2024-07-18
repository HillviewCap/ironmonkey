from flask import Blueprint, render_template
from models.allgroups import AllGroups
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from typing import List

apt_groups_bp = Blueprint('apt_groups', __name__)

@apt_groups_bp.route('/apt-groups')
def apt_groups() -> str:
    engine = create_engine('your_database_connection_string_here')
    with Session(engine) as session:
        groups: List[AllGroups] = session.query(AllGroups).all()
    return render_template('apt-groups.html', groups=groups)

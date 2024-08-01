from flask import Blueprint, render_template, request
from app.models.relational.allgroups import AllGroups, AllGroupsValues
from sqlalchemy import or_

bp = Blueprint('apt', __name__)

@bp.route('/apt-groups')
def apt_groups():
    search_query = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10

    query = AllGroups.query.join(AllGroupsValues)
    
    if search_query:
        query = query.filter(or_(
            AllGroups.name.ilike(f'%{search_query}%'),
            AllGroups.category.ilike(f'%{search_query}%'),
            AllGroups.type.ilike(f'%{search_query}%'),
            AllGroupsValues.actor.ilike(f'%{search_query}%'),
            AllGroupsValues.country.ilike(f'%{search_query}%')
        ))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    groups = pagination.items

    return render_template('apt-groups.html', groups=groups, pagination=pagination, search_query=search_query)

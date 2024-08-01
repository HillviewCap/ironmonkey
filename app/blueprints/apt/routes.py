from flask import Blueprint, render_template, request, abort
from app.models.relational.allgroups import AllGroupsValues, AllGroupsValuesNames
from sqlalchemy import or_

bp = Blueprint('apt', __name__)

@bp.route('/apt-groups')
def apt_groups():
    search_query = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10

    query = AllGroupsValues.query
    
    if search_query:
        query = query.filter(or_(
            AllGroupsValues.actor.ilike(f'%{search_query}%'),
            AllGroupsValues.country.ilike(f'%{search_query}%'),
            AllGroupsValues.description.ilike(f'%{search_query}%'),
            AllGroupsValues.motivation.ilike(f'%{search_query}%')
        ))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    groups = pagination.items

    for group in groups:
        group.names = AllGroupsValuesNames.query.filter_by(allgroups_values_uuid=group.uuid).all()

    return render_template('apt-groups.html', groups=groups, pagination=pagination, search_query=search_query)

@bp.route('/apt-group/<uuid:group_uuid>')
def apt_group_detail(group_uuid):
    group = AllGroupsValues.query.get_or_404(group_uuid)
    group.names = AllGroupsValuesNames.query.filter_by(allgroups_values_uuid=group.uuid).all()
    return render_template('apt-group-detail.html', group=group)

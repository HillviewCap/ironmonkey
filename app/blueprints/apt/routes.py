from flask import Blueprint, render_template, request, abort, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.relational.allgroups import AllGroupsValues, AllGroupsValuesNames
from app.models.relational.alltools import AllTools, AllToolsValues, AllToolsValuesNames
from app.forms import APTGroupForm
from app.extensions import db
from sqlalchemy import or_
import re
from datetime import datetime

bp = Blueprint('apt', __name__)

@bp.route('/apt-groups')
def apt_groups():
    search_query = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10

    query = AllGroupsValues.query.order_by(AllGroupsValues.last_card_change.desc())
    
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
    
    # Extract affiliate group names from description
    affiliate_pattern = r'\{\{([^}]+)\}\}'
    affiliate_matches = re.findall(affiliate_pattern, group.description)
    
    affiliate_groups = []
    for match in affiliate_matches:
        affiliate_names = [name.strip() for name in match.split(',')]
        for name in affiliate_names:
            affiliate_group = AllGroupsValues.query.join(AllGroupsValuesNames).filter(
                AllGroupsValuesNames.name == name
            ).first()
            if affiliate_group:
                affiliate_groups.append(affiliate_group)
    
    return render_template('apt-group-detail.html', group=group, affiliate_groups=affiliate_groups)

@bp.route('/apt-tool/<string:tool_name>')
def apt_tool_detail(tool_name):
    tool = AllToolsValues.query.join(AllToolsValuesNames).filter(AllToolsValuesNames.name == tool_name).first_or_404()
    return render_template('apt-tools.html', tool=tool)
def get_sector_choices():
    sectors = [
        'Energy',
        'Finance',
        'Healthcare',
        'Government',
        'Technology',
        'Defense',
        'Education',
        'Retail',
        # Add more sectors as needed
    ]
    return [(sector, sector) for sector in sectors]

def get_country_choices():
    countries = [
        'United States',
        'China',
        'Russia',
        'Iran',
        'North Korea',
        'United Kingdom',
        'Germany',
        # Add more countries as needed
    ]
    return [(country, country) for country in countries]

def get_tool_choices():
    tools = AllToolsValues.query.all()
    return [(tool.tool, tool.tool) for tool in tools]

@bp.route('/apt-group/new', methods=['GET', 'POST'])
@login_required
def create_apt_group():
    form = APTGroupForm()
    form.observed_sectors.choices = get_sector_choices()
    form.observed_countries.choices = get_country_choices()
    form.tools.choices = get_tool_choices()
    
    if form.validate_on_submit():
        new_group = AllGroupsValues(
            actor=form.actor.data,
            country=form.country.data,
            motivation=form.motivation.data,
            description=form.description.data,
            first_seen=form.first_seen.data.strftime('%Y-%m-%d') if form.first_seen.data else None,
            observed_sectors=', '.join(form.observed_sectors.data),
            observed_countries=', '.join(form.observed_countries.data),
            tools=', '.join(form.tools.data),
            last_card_change=datetime.utcnow().strftime('%Y-%m-%d'),
        )
        db.session.add(new_group)
        db.session.commit()
        flash('New APT group created successfully!', 'success')
        return redirect(url_for('apt.apt_group_detail', group_uuid=new_group.uuid))
    return render_template('apt-group-form.html', form=form)

@bp.route('/apt-group/<uuid:group_uuid>/edit', methods=['GET', 'POST'])
@login_required
def edit_apt_group(group_uuid):
    group = AllGroupsValues.query.get_or_404(group_uuid)
    form = APTGroupForm(obj=group)
    form.observed_sectors.choices = get_sector_choices()
    form.observed_countries.choices = get_country_choices()
    form.tools.choices = get_tool_choices()
    
    if request.method == 'GET':
        form.observed_sectors.data = (group.observed_sectors or '').split(', ')
        form.observed_countries.data = (group.observed_countries or '').split(', ')
        form.tools.data = (group.tools or '').split(', ')
        if group.first_seen:
            form.first_seen.data = datetime.strptime(group.first_seen, '%Y-%m-%d')
    
    if form.validate_on_submit():
        group.actor = form.actor.data
        group.country = form.country.data
        group.motivation = form.motivation.data
        group.description = form.description.data
        group.first_seen = form.first_seen.data.strftime('%Y-%m-%d') if form.first_seen.data else None
        group.observed_sectors = ', '.join(form.observed_sectors.data)
        group.observed_countries = ', '.join(form.observed_countries.data)
        group.tools = ', '.join(form.tools.data)
        group.last_card_change = datetime.utcnow().strftime('%Y-%m-%d')
        db.session.commit()
        flash('APT group updated successfully!', 'success')
        return redirect(url_for('apt.apt_group_detail', group_uuid=group.uuid))
    return render_template('apt-group-form.html', form=form, group=group)

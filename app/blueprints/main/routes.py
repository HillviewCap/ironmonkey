from flask import render_template, send_from_directory, redirect, url_for, abort, current_app, jsonify
from flask_login import current_user, login_required
import os
from app.models.relational.parsed_content import ParsedContent
from app.models.relational.rss_feed import RSSFeed
from . import bp
from datetime import datetime, time
from sqlalchemy import desc
from app.services.news_rollup_service import NewsRollupService

@bp.route('/about')
def about():
    """Render the About page."""
    return render_template('about.html')

@bp.app_template_filter('format_date')
def format_date(value):
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(value, str):
        try:
            return datetime.strptime(value, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            return value
    return str(value)

@bp.route('/')
@login_required
def index():
    """
    Render the index page.
    
    Display the 6 most recent parsed content items for authenticated users.
    
    Returns:
        str: Rendered HTML template for the index page.
    """
    current_app.logger.info("Entering index route")
    try:
        recent_items = (
            db.session.query(ParsedContent, RSSFeed.title.label('feed_title'))
            .join(RSSFeed)
            .filter(
                ParsedContent.title.isnot(None),
                ParsedContent.description.isnot(None),
            )
            .order_by(ParsedContent.pub_date.desc())
            .limit(6)
            .all()
        )
        current_time = datetime.now().time()
        midday_time = time(12, 0)
        end_of_day_time = time(18, 0)
        
        # Get the rollup types that already exist for today
        existing_rollups = NewsRollupService.get_rollup_types_for_today()
        
        current_app.logger.info(f"User {current_user.id} accessed index route.")
        return render_template('index.html', 
                               recent_items=recent_items,
                               current_time=current_time,
                               midday_time=midday_time,
                               end_of_day_time=end_of_day_time,
                               existing_rollups=existing_rollups)
    except Exception as e:
        current_app.logger.error(f"Error in index route: {str(e)}")
        abort(500)  # Return a 500 Internal Server Error

@bp.route('/generate_rollup/<rollup_type>')
@login_required
async def generate_single_rollup(rollup_type):
    service = NewsRollupService()
    try:
        existing_rollup = service.get_latest_rollup(rollup_type)
        if existing_rollup:
            rollup = existing_rollup['content']
            audio_url = url_for('static', filename=f'audio/{os.path.basename(existing_rollup["audio_file"])}') if existing_rollup['audio_file'] else None
        else:
            rollup = await service.generate_rollup(rollup_type)
            if isinstance(rollup, dict) and 'error' in rollup:
                current_app.logger.error(f"Error in rollup generation: {rollup['error']}")
                return render_template('rollup.html', rollup_type=rollup_type, rollup_content=rollup)
            
            audio_file = service.generate_audio_rollup(rollup, rollup_type)
            audio_url = url_for('static', filename=f'audio/{os.path.basename(audio_file)}') if audio_file else None
            
            # Store the new rollup
            await service.create_and_store_rollup(rollup_type)
        
        return render_template('rollup.html', rollup_type=rollup_type, rollup_content=rollup, audio_url=audio_url)
    except ValueError as e:
        current_app.logger.error(f"Invalid rollup type: {str(e)}")
        return render_template('rollup.html', rollup_type=rollup_type, rollup_content={'error': "Invalid rollup type"})
    except Exception as e:
        current_app.logger.error(f"Error generating rollup: {str(e)}")
        return render_template('rollup.html', rollup_type=rollup_type, rollup_content={'error': "Failed to generate rollup"})

@bp.route('/apt-groups')
def apt_groups():
    return redirect(url_for('apt.apt_groups'))

@bp.route('/item/<uuid:item_id>')
@login_required
def view_item(item_id):
    """
    Render the page for a specific parsed content item.
    
    Args:
        item_id (uuid): The UUID of the parsed content item to display.
    
    Returns:
        str: Rendered HTML template for the item view page.
    
    Raises:
        404: If the item with the given UUID is not found.
    """
    item = ParsedContent.query.get(item_id)
    if item is None:
        abort(404)
    return render_template('view_item.html', item=item)

@bp.route('/favicon.ico')
def favicon():
    """
    Serve the favicon.ico file.
    
    Returns:
        flask.Response: The favicon.ico file.
    """
    return send_from_directory(os.path.join(current_app.root_path, 'static', 'images'),
                               'favicon.ico', mimetype='image/x-icon')

@bp.errorhandler(500)
def internal_error(error):
    """
    Handle 500 Internal Server Error.
    
    Args:
        error: The error that caused the 500 status.
    
    Returns:
        tuple: A tuple containing the rendered error template and the 500 status code.
    """
    current_app.logger.error('Server Error: %s', (error))
    return render_template('errors/500.html'), 500

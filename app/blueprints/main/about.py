from flask import render_template
from . import bp

@bp.route('/about')
def about():
    """Render the About page."""
    return render_template('about.html')

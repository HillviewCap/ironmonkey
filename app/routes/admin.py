from flask import flash, redirect, url_for
from flask_login import login_required
from app.services.awesome_threat_intel_service import AwesomeThreatIntelService
from app.decorators import admin_required
from app import admin

@admin.route('/update_awesome_threat_intel', methods=['POST'])
@login_required
@admin_required
def update_awesome_threat_intel():
    AwesomeThreatIntelService.update_from_csv()
    flash('Awesome Threat Intel Blogs have been updated.', 'success')
    return redirect(url_for('admin.rss_feeds'))

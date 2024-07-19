from app.services.awesome_threat_intel_service import AwesomeThreatIntelService

@admin.route('/update_awesome_threat_intel', methods=['POST'])
@login_required
@admin_required
def update_awesome_threat_intel():
    AwesomeThreatIntelService.update_from_csv()
    flash('Awesome Threat Intel Blogs have been updated.', 'success')
    return redirect(url_for('admin.rss_feeds'))

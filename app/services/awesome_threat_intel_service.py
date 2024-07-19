import os
from flask import current_app
from app.models.relational.awesome_threat_intel_blog import AwesomeThreatIntelBlog
from app.services.awesome_threat_intel_service import AwesomeThreatIntelService
from app import db
import csv
from datetime import datetime

class AwesomeThreatIntelService:
    @staticmethod
    def update_from_csv():
        """
        Check the CSV file for new items and update the awesome_threat_intel_blog table.
        """
        csv_file_path = os.path.join(current_app.root_path, 'static', 'Awesome Threat Intel Blogs - MASTER.csv')
        
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                AwesomeThreatIntelBlog.update_or_create(
                    blog=row['Blog'],
                    blog_category=row['Blog Category'],
                    type=row['Type'],
                    blog_link=row['Blog Link'],
                    feed_link=row['Feed Link'],
                    feed_type=row['Feed Type']
                )
        
        # Update last_checked for all entries
        AwesomeThreatIntelBlog.query.update({AwesomeThreatIntelBlog.last_checked: datetime.utcnow()})
        db.session.commit()

    @staticmethod
    def get_update_status():
        """
        Get the status of the last update.

        Returns:
            dict: A dictionary containing the update status and timestamp.
        """
        last_checked = db.session.query(db.func.max(AwesomeThreatIntelBlog.last_checked)).scalar()
        return {
            "last_updated": last_checked.isoformat() if last_checked else None,
            "status": "Up to date" if last_checked else "Never updated"
        }

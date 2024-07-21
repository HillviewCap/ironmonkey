"""
This module provides services for managing Awesome Threat Intel Blogs.

It includes functionality for updating the database from a CSV file and
retrieving the update status.
"""

import os
from flask import current_app
from app.models.relational.awesome_threat_intel_blog import AwesomeThreatIntelBlog
from app import db
import csv
from datetime import datetime

class AwesomeThreatIntelService:
    """
    A service class for managing Awesome Threat Intel Blogs.

    This class provides static methods for updating the database from a CSV file
    and retrieving the update status.
    """
    @staticmethod
    def update_from_csv():
        """
        Check the CSV file for new items and update the awesome_threat_intel_blog table.

        This method reads a CSV file containing Awesome Threat Intel Blog information,
        updates existing entries, and adds new ones to the database. It also updates
        the last_checked timestamp for all entries.

        The CSV file is expected to be located at:
        [app_root_path]/static/Awesome Threat Intel Blogs - MASTER.csv

        Returns:
            None
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
        Get the status of the last update for Awesome Threat Intel Blogs.

        This method queries the database to find the most recent last_checked
        timestamp among all Awesome Threat Intel Blog entries.

        Returns:
            dict: A dictionary containing the update status and timestamp.
                  The dictionary has two keys:
                  - 'last_updated': ISO formatted timestamp of the last update,
                                    or None if never updated.
                  - 'status': Either "Up to date" if there's a last_checked timestamp,
                              or "Never updated" if there isn't.
        """
        last_checked = db.session.query(db.func.max(AwesomeThreatIntelBlog.last_checked)).scalar()
        return {
            "last_updated": last_checked.isoformat() if last_checked else None,
            "status": "Up to date" if last_checked else "Never updated"
        }

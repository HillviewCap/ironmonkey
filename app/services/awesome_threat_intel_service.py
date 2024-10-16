"""
This module provides services for managing Awesome Threat Intel Blogs.

It includes functionality for updating the database from a CSV file and
retrieving the update status.
"""

import os
import uuid
from flask import current_app
from app.models.relational.awesome_threat_intel_blog import AwesomeThreatIntelBlog
from app import db
import csv
from datetime import datetime
from uuid import UUID
from sqlalchemy import text

class AwesomeThreatIntelService:
    """
    A service class for managing Awesome Threat Intel Blogs.

    This class provides static methods for updating the database from a CSV file
    and retrieving the update status.
    """
    @staticmethod
    def update_from_csv():
        """
        Update Awesome Threat Intel Blogs from CSV file.

        This method reads the CSV file, compares it with existing entries in the database,
        adds new entries, updates existing ones, and removes entries that are no longer in the CSV.
        """
        csv_file_path = os.path.join(current_app.root_path, 'static', 'Awesome Threat Intel Blogs - MASTER.csv')
        existing_blogs = {blog.blog: blog for blog in AwesomeThreatIntelBlog.query.all()}
        csv_blogs = set()

        try:
            with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                # Print column names
                print("CSV columns:", reader.fieldnames)
                
                # Read and print the first row
                first_row = next(reader, None)
                if first_row:
                    print("First row data:", first_row)
                else:
                    print("CSV file is empty")
                    return
                
                # Reset the reader to the beginning of the file
                csvfile.seek(0)
                next(reader)  # Skip the header row
                
                for row in reader:
                    blog_name = row.get('Blog Name')
                    if not blog_name:
                        print(f"Warning: 'Blog Name' column not found in row: {row}")
                        continue
                    
                    csv_blogs.add(blog_name)
                    
                    if blog_name in existing_blogs:
                        # Update existing blog
                        blog = existing_blogs[blog_name]
                        blog.blog_category = row.get('Blog Category', '')
                        blog.type = row.get('Type', '')
                        blog.blog_link = row.get('Blog Link', '')
                        blog.feed_link = row.get('Feed Link', '')
                        blog.feed_type = row.get('Feed Type', '')
                    else:
                        # Add new blog with a proper UUID
                        blog = AwesomeThreatIntelBlog(
                            id=uuid.uuid4(),  # Generate a new UUID for each new blog
                            blog=blog_name,
                            blog_category=row.get('Blog Category', ''),
                            type=row.get('Type', ''),
                            blog_link=row.get('Blog Link', ''),
                            feed_link=row.get('Feed Link', ''),
                            feed_type=row.get('Feed Type', '')
                        )
                        db.session.add(blog)
                    
                    # Update last_checked for each entry
                    blog.last_checked = datetime.utcnow()
        except FileNotFoundError:
            print(f"Error: CSV file not found at {csv_file_path}")
            return
        except csv.Error as e:
            print(f"Error reading CSV file: {e}")
            return

        # Remove blogs that are not in the CSV
        for blog_name, blog in existing_blogs.items():
            if blog_name not in csv_blogs:
                db.session.delete(blog)

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

    @staticmethod
    def initialize_awesome_feeds():
        """
        Check if the Awesome Threat Intel Blogs table is empty and load feeds if necessary.

        This method checks if there are any entries in the AwesomeThreatIntelBlog table.
        If the table is empty, it calls the update_from_csv method to load the feeds.
        """
        try:
            if AwesomeThreatIntelBlog.query.first() is None:
                AwesomeThreatIntelService.update_from_csv()
                print("Awesome Threat Intel Blogs initialized successfully.")
            else:
                print("Awesome Threat Intel Blogs already initialized.")
        except Exception as e:
            print(f"Error initializing awesome feeds: {e}")
            # You might want to log the error or raise a custom exception here

    @staticmethod
    def cleanup_awesome_threat_intel_blog_ids():
        # First, let's identify any problematic IDs
        problematic_ids = db.session.execute(text("SELECT id FROM awesome_threat_intel_blog WHERE id ~ '^[0-9]+$'")).fetchall()
        
        for (id_value,) in problematic_ids:
            try:
                # Try to convert the integer to a UUID
                new_uuid = UUID(int=int(id_value))
            except ValueError:
                # If the int is too large for UUID, generate a new UUID
                new_uuid = uuid.uuid4()
            
            # Update the ID in the database
            db.session.execute(
                text("UPDATE awesome_threat_intel_blog SET id = :new_uuid WHERE id = :old_id"),
                {"new_uuid": str(new_uuid), "old_id": id_value}
            )
        
        db.session.commit()
        print(f"Cleanup of {len(problematic_ids)} Awesome Threat Intel Blog IDs completed.")

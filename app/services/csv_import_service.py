"""
This module provides services for importing RSS feeds from CSV files.

It includes functionality for processing CSV files, adding new RSS feeds to the database,
and handling errors during the import process.
"""

from typing import TextIO, Tuple, List
from io import TextIOWrapper
import csv
from flask import current_app
from sqlalchemy.exc import IntegrityError
from app.models import db, RSSFeed

def process_csv_file(csv_file: TextIO) -> Tuple[int, int, List[str]]:
    """
    Process the uploaded CSV file and return import statistics.

    This function reads a CSV file containing RSS feed information, attempts to add
    each feed to the database, and keeps track of successful imports, skipped entries,
    and any errors encountered.

    Args:
        csv_file (TextIO): A file-like object containing the CSV data.

    Returns:
        Tuple[int, int, List[str]]: A tuple containing:
            - The number of successfully imported feeds
            - The number of skipped feeds (due to duplicates)
            - A list of error messages for any feeds that couldn't be processed
    """
    imported_count, skipped_count = 0, 0
    errors: List[str] = []
    csv_file = TextIOWrapper(csv_file, encoding="utf-8")
    csv_reader = csv.reader(csv_file)

    # Skip the header row
    next(csv_reader, None)

    for row in csv_reader:
        if len(row) >= 1:
            url = row[0]
            category = row[1] if len(row) > 1 else "Uncategorized"
            try:
                title, description, last_build_date = RSSFeed.fetch_feed_info(url)
                new_feed = RSSFeed(
                    url=url,
                    title=title,
                    category=category,
                    description=description,
                    last_build_date=last_build_date,
                )
                db.session.add(new_feed)
                db.session.commit()
                imported_count += 1
                current_app.logger.info(f"RSS Feed added from CSV: {url}")
            except IntegrityError:
                db.session.rollback()
                skipped_count += 1
                current_app.logger.info(f"Skipped duplicate RSS Feed: {url}")
            except Exception as e:
                errors.append(f"Error processing RSS Feed {url}: {str(e)}")
                current_app.logger.error(
                    f"Error processing RSS Feed {url}: {str(e)}"
                )

    return imported_count, skipped_count, errors

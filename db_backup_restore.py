import sqlite3
import json
import os
from datetime import datetime
import argparse
from pathlib import Path

def backup_schema(cursor, table):
    cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'")
    result = cursor.fetchone()
    if result is None:
        return None
    return result[0]

def backup_tables(source_db, backup_dir):
    # Connect to the source database
    conn = sqlite3.connect(source_db)
    cursor = conn.cursor()

    # Tables to backup
    tables = ['parsed_content', 'parsed_content_categories', 'rss_feed', 'category']

    # Create backup directory if it doesn't exist
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    # Get current timestamp for the backup file names
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for table in tables:
        # Backup schema
        schema = backup_schema(cursor, table)
        
        if schema is None:
            print(f"Table {table} does not exist in the database. Skipping.")
            continue
        
        # Fetch all data from the table
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()

        # Get column names
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [column[1] for column in cursor.fetchall()]

        # Prepare data as a list of dictionaries
        data = [dict(zip(columns, row)) for row in rows]

        # Prepare backup data including schema and table data
        backup_data = {
            'schema': schema,
            'data': data
        }

        # Write data to a JSON file
        backup_file = os.path.join(backup_dir, f"{table}_backup_{timestamp}.json")
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)

        print(f"Backed up {table} to {backup_file}")

    # Close the database connection
    conn.close()

def restore_tables(backup_dir, target_db):
    # Connect to the target database
    conn = sqlite3.connect(target_db)
    cursor = conn.cursor()

    # Enable foreign key support
    cursor.execute("PRAGMA foreign_keys = OFF;")

    # Define the order of table restoration
    table_order = ['category', 'rss_feed', 'parsed_content', 'parsed_content_categories']

    # Get all JSON files in the backup directory
    backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.json')]

    for table_name in table_order:
        backup_file = next((f for f in backup_files if f.startswith(f"{table_name}_backup_")), None)
        
        if backup_file:
            # Read data from the JSON file
            with open(os.path.join(backup_dir, backup_file), 'r') as f:
                backup_data = json.load(f)

            # Extract schema and data
            schema = backup_data['schema']
            data = backup_data['data']

            if data:
                # Create the table using the backed-up schema
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
                cursor.execute(schema)

                # Get column names from the first item in the data
                columns = list(data[0].keys())

                # Insert data into the table
                placeholders = ', '.join(['?' for _ in columns])
                insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                
                for row in data:
                    cursor.execute(insert_sql, [row.get(col) for col in columns])

                print(f"Restored {table_name} from {backup_file}")

    # Re-enable foreign key support
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Commit changes and close the connection
    conn.commit()
    conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backup or restore SQLite database")
    parser.add_argument("--backup", action="store_true", help="Perform database backup")
    parser.add_argument("--restore", action="store_true", help="Perform database restore")
    args = parser.parse_args()

    source_db = os.path.join("instance", "threats.db")
    backup_dir = "db_backup"
    target_db = os.path.join("instance", "new_threats.db")

    if args.backup:
        backup_tables(source_db, backup_dir)
    elif args.restore:
        restore_tables(backup_dir, target_db)
    else:
        print("Please specify either --backup or --restore")

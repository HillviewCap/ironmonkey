import sqlite3
import shutil
from datetime import datetime
import os

DB_PATH = "instance/threats.db"
BACKUP_PATH = "instance/threats_backup.db"

def backup_database():
    shutil.copy2(DB_PATH, BACKUP_PATH)

def restore_database():
    shutil.copy2(BACKUP_PATH, DB_PATH)

def convert_date(date_string):
    try:
        return datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None

def apply_patch():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Create new table
        cursor.execute("""
        CREATE TABLE parsed_content_new (
            id INTEGER PRIMARY KEY,
            title TEXT,
            description TEXT,
            content TEXT,
            link TEXT,
            pub_date TIMESTAMP,
            -- Add other columns as needed
        )
        """)

        # Copy data
        cursor.execute("""
        INSERT INTO parsed_content_new (id, title, description, content, link, pub_date)
        SELECT id, title, description, content, link, 
               CASE 
                   WHEN pub_date IS NOT NULL AND pub_date != '' 
                   THEN datetime(pub_date) 
                   ELSE NULL 
               END
        FROM parsed_content
        """)

        # Rename tables
        cursor.execute("DROP TABLE parsed_content")
        cursor.execute("ALTER TABLE parsed_content_new RENAME TO parsed_content")

        conn.commit()
        print("Patch applied successfully")
        return True

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        conn.rollback()
        return False

    finally:
        conn.close()

def main():
    backup_database()
    
    if apply_patch():
        os.remove(BACKUP_PATH)
        print("Backup deleted")
    else:
        restore_database()
        print("Patch failed, database restored from backup")

if __name__ == "__main__":
    main()

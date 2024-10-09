import sqlite3
import shutil
from datetime import datetime
import os
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

def log(message, color=Fore.WHITE, style=Style.NORMAL):
    print(f"{style}{color}{message}{Style.RESET_ALL}")

DB_PATH = "instance/threats.db"
BACKUP_PATH = "instance/threats_backup.db"

def backup_database():
    shutil.copy2(DB_PATH, BACKUP_PATH)
    log("Database backed up successfully.", Fore.GREEN)

def restore_database():
    shutil.copy2(BACKUP_PATH, DB_PATH)
    log("Database restored from backup.", Fore.YELLOW)

def convert_date(date_string):
    try:
        return datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None

def apply_patch():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        log("Starting database patch process...", Fore.CYAN)

        log("Creating new table...", Fore.YELLOW)
        cursor.execute("""
        CREATE TABLE parsed_content_new (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            description TEXT,
            content TEXT NOT NULL,
            summary TEXT,
            feed_id TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL,
            pub_date TIMESTAMP NOT NULL,
            creator TEXT,
            art_hash TEXT
        )
        """)

        log("Copying data to new table...", Fore.YELLOW)
        cursor.execute("""
        INSERT INTO parsed_content_new (
            id, title, url, description, content, summary, feed_id, 
            created_at, pub_date, creator, art_hash
        )
        SELECT 
            id, title, url, description, content, summary, feed_id,
            COALESCE(created_at, CURRENT_TIMESTAMP),
            CASE 
                WHEN pub_date IS NOT NULL AND pub_date != '' 
                THEN datetime(pub_date) 
                ELSE CURRENT_TIMESTAMP 
            END,
            creator, art_hash
        FROM parsed_content
        """)

        log("Renaming tables...", Fore.YELLOW)
        cursor.execute("DROP TABLE parsed_content")
        cursor.execute("ALTER TABLE parsed_content_new RENAME TO parsed_content")

        conn.commit()
        log("Patch applied successfully", Fore.GREEN, Style.BRIGHT)
        return True

    except sqlite3.Error as e:
        log(f"An error occurred: {e}", Fore.RED, Style.BRIGHT)
        conn.rollback()
        return False

    finally:
        conn.close()

def main():
    log("Starting database patch process...", Fore.CYAN, Style.BRIGHT)
    backup_database()
    
    if apply_patch():
        os.remove(BACKUP_PATH)
        log("Backup deleted", Fore.GREEN)
        log("Database patch completed successfully!", Fore.GREEN, Style.BRIGHT)
    else:
        restore_database()
        log("Patch failed, database restored from backup", Fore.RED, Style.BRIGHT)

if __name__ == "__main__":
    main()

import sqlite3
import json
from typing import List, Dict
from datetime import datetime

def send_to_sqlite(jobs: List[Dict], table_name: str, db_path: str = "sponsorship_scout.db"):
    if not jobs:
        return
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table if not exists
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT,
            title TEXT,
            location TEXT,
            url TEXT UNIQUE,
            added_date TEXT
        )
    ''')
    
    new_jobs_count = 0
    today = datetime.now().strftime('%Y-%m-%d')
    
    for job in jobs:
        try:
            cursor.execute(f'''
                INSERT INTO {table_name} (company, title, location, url, added_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (job['company'], job['title'], job['location'], job['url'], today))
            new_jobs_count += 1
        except sqlite3.IntegrityError:
            pass # Job URL already exists
            
    conn.commit()
    conn.close()
    if new_jobs_count > 0:
        print(f"Saved {new_jobs_count} new jobs to SQLite table {table_name}.")

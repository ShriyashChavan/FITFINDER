import sqlite3
import os

DB_NAME = os.path.join(os.path.dirname(__file__), "users.db")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        userid TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    # Insert a default allowed user (change these credentials)
    cur.execute("INSERT OR IGNORE INTO users (userid, password) VALUES (?, ?)", ("admin123", "Secret@123"))

    conn.commit()
    conn.close()
    print(f"DB initialized at: {DB_NAME}")

if __name__ == '__main__':
    init_db()

from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).with_name("voloveteer.db")

def get_db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_db() as connection:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                location TEXT NOT NOT NULL,
                date_text TEXT NOT NULL,
                organizer TEXT NOT NULL,
                contact_email TEXT,
                registration_url TEXT,
                active INTEGER NOT NULL DEFAULT 1
            );
        """)


if __name__ == "__main__":
    init_db()
    print(f"Initialized {DB_PATH}")

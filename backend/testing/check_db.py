
import sqlite3
from pathlib import Path

db_path = Path("vibanu.db")

print("Database path:", db_path.resolve())

if not db_path.exists():
    print("Database file does not exist yet.")
else:
    with sqlite3.connect(db_path) as connection:
        query = """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name
        """

        tables = connection.execute(query).fetchall()
        print("Tables found:", tables)

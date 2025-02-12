import sqlite3
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_name="chat_history.db"):
        self.conn = sqlite3.connect(db_name)
        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute(
            '''CREATE TABLE IF NOT EXISTS chat_summaries
               (id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                summary TEXT,
                model_used TEXT,
                token_count INT)'''
        )
        self.conn.commit()

    def save_summary(self, summary_data):
        cursor = self.conn.cursor()
        cursor.execute(
            '''INSERT INTO chat_summaries 
               (timestamp, summary, model_used, token_count)
               VALUES (?, ?, ?, ?)''',
            (datetime.now(), summary_data['summary'], summary_data['model'], summary_data['tokens'])
        )
        self.conn.commit()
        return True

    def load_summaries(self, limit=5):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT summary FROM chat_summaries ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        return "\n".join([row[0] for row in cursor.fetchall()])

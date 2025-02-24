import sqlite3
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute(
            '''CREATE TABLE IF NOT EXISTS chat_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                summary TEXT,
                chat_history TEXT,
                model_used TEXT,
                token_count INT,
                user_id TEXT
            )'''
        )
        cursor.execute(
            '''CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                created_at DATETIME
            )'''
        )
        cursor.execute(
            '''CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                creator_id TEXT,
                name TEXT,
                description TEXT,
                llm_model TEXT,
                instruction_prompt TEXT,
                response_style TEXT,
                creativity REAL,
                response_length TEXT,
                welcome_message TEXT,
                language TEXT,
                restricted_words TEXT,
                resources TEXT,
                created_at DATETIME,
                updated_at DATETIME
            )'''
        )
        cursor.execute(
            '''CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                agent_id TEXT,
                chatbot_name TEXT,
                model_name TEXT,
                temperature REAL,
                title TEXT,
                created_at DATETIME,
                updated_at DATETIME,
                last_message_at DATETIME
            )'''
        )
        cursor.execute(
            '''CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT,
                role TEXT,
                content TEXT,
                tokens_used INTEGER,
                created_at DATETIME,
                file_ids TEXT
            )'''
        )
        self.conn.commit()

    def register_user(self, user_id):
        cursor = self.conn.cursor()
        now = datetime.now()
        try:
            cursor.execute("INSERT INTO users (id, created_at) VALUES (?, ?)", (user_id, now))
            self.conn.commit()
            return {"id": user_id, "created_at": now.isoformat()}
        except sqlite3.IntegrityError:
            return None

    def create_agent(self, agent_data):
        cursor = self.conn.cursor()
        now = datetime.now()
        try:
            cursor.execute(
                '''INSERT INTO agents (id, creator_id, name, description, llm_model, instruction_prompt, response_style, creativity, response_length, welcome_message, language, restricted_words, resources, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    agent_data.get("id"),
                    agent_data.get("creator_id"),
                    agent_data.get("name"),
                    agent_data.get("description"),
                    agent_data.get("llm_model"),
                    agent_data.get("instruction_prompt"),
                    agent_data.get("response_style"),
                    agent_data.get("creativity"),
                    agent_data.get("response_length"),
                    agent_data.get("welcome_message"),
                    agent_data.get("language"),
                    ",".join(agent_data.get("restricted_words", [])),
                    ",".join(agent_data.get("resources", [])),
                    now,
                    now
                )
            )
            self.conn.commit()
            agent_data["created_at"] = now.isoformat()
            agent_data["updated_at"] = now.isoformat()
            return agent_data
        except Exception as e:
            print(e)
            return None

    def update_agent(self, agent_id, agent_data):
        cursor = self.conn.cursor()
        now = datetime.now()
        try:
            set_clauses = []
            values = []
            for key, value in agent_data.items():
                if key in ["restricted_words", "resources"] and isinstance(value, list):
                    value = ",".join(value)
                set_clauses.append(f"{key}=?")
                values.append(value)
            set_clauses.append("updated_at=?")
            values.append(now)
            values.append(agent_id)
            query = f"UPDATE agents SET {', '.join(set_clauses)} WHERE id=?"
            cursor.execute(query, tuple(values))
            self.conn.commit()
            return self.get_agent(agent_id)
        except Exception as e:
            print(e)
            return None

    def get_agent(self, agent_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM agents WHERE id=?", (agent_id,))
        row = cursor.fetchone()
        if row:
            columns = [desc[0] for desc in cursor.description]
            agent = dict(zip(columns, row))
            agent["restricted_words"] = agent.get("restricted_words", "").split(",") if agent.get("restricted_words") else []
            agent["resources"] = agent.get("resources", "").split(",") if agent.get("resources") else []
            return agent
        return None

    def delete_agent(self, agent_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM agents WHERE id=?", (agent_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def list_conversations(self, user_id, page=1, limit=20):
        offset = (page - 1) * limit
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM conversations WHERE user_id=? ORDER BY last_message_at DESC LIMIT ? OFFSET ?",
            (user_id, limit, offset)
        )
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

    def create_conversation(self, conversation_data):
        cursor = self.conn.cursor()
        now = datetime.now()
        conversation_id = conversation_data.get("id")
        cursor.execute(
            '''INSERT INTO conversations (id, user_id, agent_id, chatbot_name, model_name, temperature, title, created_at, updated_at, last_message_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (
                conversation_id,
                conversation_data.get("user_id"),
                conversation_data.get("agent_id"),
                conversation_data.get("chatbot_name"),
                conversation_data.get("model_name"),
                conversation_data.get("temperature"),
                conversation_data.get("title"),
                now, now, now
            )
        )
        self.conn.commit()
        conversation_data["created_at"] = now.isoformat()
        conversation_data["updated_at"] = now.isoformat()
        conversation_data["last_message_at"] = now.isoformat()
        return conversation_data

    def save_summary(self, summary_data):
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                '''INSERT INTO chat_summaries 
                   (timestamp, summary, chat_history, model_used, token_count, user_id)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (
                    datetime.now(),
                    summary_data['summary'],
                    summary_data['chat_history'],
                    summary_data['model'],
                    summary_data['tokens'],
                    summary_data['user_id']
                )
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(e)
            return False

    def list_messages(self, conversation_id, page=1, limit=50):
        offset = (page - 1) * limit
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM messages WHERE conversation_id=? ORDER BY created_at ASC LIMIT ? OFFSET ?",
            (conversation_id, limit, offset)
        )
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

    def create_message(self, message_data):
        cursor = self.conn.cursor()
        now = datetime.now()
        message_id = message_data.get("id")
        file_ids = ",".join(message_data.get("file_ids", []))
        cursor.execute(
            '''INSERT INTO messages (id, conversation_id, role, content, tokens_used, created_at, file_ids)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (
                message_id,
                message_data.get("conversation_id"),
                message_data.get("role"),
                message_data.get("content"),
                message_data.get("tokens_used"),
                now,
                file_ids
            )
        )
        self.conn.commit()
        message_data["created_at"] = now.isoformat()
        return message_data

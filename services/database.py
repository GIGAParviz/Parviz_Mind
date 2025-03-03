import sqlite3
import uuid
import json
from datetime import datetime
from typing import List, Dict, Optional, Any

from config import Config

class DatabaseManager:
    """Manager for database operations."""
    
    def __init__(self, db_name=None):
        """Initialize the database manager."""
        self.db_name = db_name or Config.DATABASE_PATH
        self._create_tables()
        
    def _create_tables(self):
        """Create database tables if they don't exist."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Agents table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                level TEXT NOT NULL,
                hourly_rate REAL NOT NULL,
                specialties TEXT,
                languages TEXT,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Agent ratings table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_ratings (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                rating REAL NOT NULL,
                feedback TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (agent_id) REFERENCES agents (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            ''')
            
            # Conversations table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                model TEXT NOT NULL,
                language TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            ''')
            
            # Messages table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id)
            )
            ''')
            
            # Summaries table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS summaries (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                summary TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id)
            )
            ''')
            
            # Agent conversations table (for handoffs)
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_conversations (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                conversation_id TEXT NOT NULL,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                duration_minutes REAL,
                status TEXT NOT NULL,
                FOREIGN KEY (agent_id) REFERENCES agents (id),
                FOREIGN KEY (conversation_id) REFERENCES conversations (id)
            )
            ''')
            
            conn.commit()
    
    def register_user(self, user_id):
        """Register a new user."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO users (id) VALUES (?)",
                (user_id,)
            )
            conn.commit()
            
            return {"id": user_id}
    
    def create_agent(self, agent_data):
        """Create a new agent."""
        agent_id = agent_data.get("agent_id") or str(uuid.uuid4())
        specialties = json.dumps(agent_data.get("specialties", []))
        languages = json.dumps(agent_data.get("languages", []))
        
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            
            cursor.execute(
                """
                INSERT INTO agents 
                (id, name, level, hourly_rate, specialties, languages, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    agent_id,
                    agent_data["name"],
                    agent_data["level"],
                    agent_data["hourly_rate"],
                    specialties,
                    languages,
                    agent_data.get("status", "offline"),
                    now,
                    now
                )
            )
            conn.commit()
            
            return self.get_agent(agent_id)
    
    def update_agent(self, agent_id, agent_data):
        """Update an existing agent."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            
            # Build the update query dynamically based on provided fields
            update_parts = []
            params = []
            
            if "name" in agent_data:
                update_parts.append("name = ?")
                params.append(agent_data["name"])
                
            if "level" in agent_data:
                update_parts.append("level = ?")
                params.append(agent_data["level"])
                
            if "hourly_rate" in agent_data:
                update_parts.append("hourly_rate = ?")
                params.append(agent_data["hourly_rate"])
                
            if "specialties" in agent_data:
                update_parts.append("specialties = ?")
                params.append(json.dumps(agent_data["specialties"]))
                
            if "languages" in agent_data:
                update_parts.append("languages = ?")
                params.append(json.dumps(agent_data["languages"]))
                
            if "status" in agent_data:
                update_parts.append("status = ?")
                params.append(agent_data["status"])
                
            update_parts.append("updated_at = ?")
            params.append(now)
            
            # Add the agent_id to params
            params.append(agent_id)
            
            # Execute the update
            cursor.execute(
                f"""
                UPDATE agents 
                SET {", ".join(update_parts)}
                WHERE id = ?
                """,
                params
            )
            conn.commit()
            
            if cursor.rowcount == 0:
                raise ValueError(f"Agent with ID {agent_id} not found")
                
            return self.get_agent(agent_id)
    
    def get_agent(self, agent_id):
        """Get agent details."""
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM agents WHERE id = ?",
                (agent_id,)
            )
            
            row = cursor.fetchone()
            
            if not row:
                raise ValueError(f"Agent with ID {agent_id} not found")
                
            # Calculate average rating
            cursor.execute(
                "SELECT AVG(rating) as avg_rating FROM agent_ratings WHERE agent_id = ?",
                (agent_id,)
            )
            
            avg_rating = cursor.fetchone()["avg_rating"]
            
            agent = dict(row)
            agent["specialties"] = json.loads(agent["specialties"]) if agent["specialties"] else []
            agent["languages"] = json.loads(agent["languages"]) if agent["languages"] else []
            agent["rating"] = avg_rating
            
            return agent
    
    def delete_agent(self, agent_id):
        """Delete an agent."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                "DELETE FROM agents WHERE id = ?",
                (agent_id,)
            )
            conn.commit()
            
            if cursor.rowcount == 0:
                raise ValueError(f"Agent with ID {agent_id} not found")
                
            return {"success": True, "message": f"Agent {agent_id} deleted successfully"}
    
    def list_conversations(self, user_id, page=1, limit=20):
        """List conversations for a user."""
        offset = (page - 1) * limit
        
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT * FROM conversations 
                WHERE user_id = ? 
                ORDER BY updated_at DESC
                LIMIT ? OFFSET ?
                """,
                (user_id, limit, offset)
            )
            
            rows = cursor.fetchall()
            conversations = [dict(row) for row in rows]
            
            return conversations
    
    def create_conversation(self, conversation_data):
        """Create a new conversation."""
        conversation_id = str(uuid.uuid4())
        
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            
            cursor.execute(
                """
                INSERT INTO conversations 
                (id, user_id, title, model, language, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    conversation_id,
                    conversation_data["user_id"],
                    conversation_data["title"],
                    conversation_data["model"],
                    conversation_data["language"],
                    now,
                    now
                )
            )
            conn.commit()
            
            # Return the created conversation
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM conversations WHERE id = ?",
                (conversation_id,)
            )
            
            row = cursor.fetchone()
            conversation = dict(row)
            
            return conversation
    
    def save_summary(self, summary_data):
        """Save a conversation summary."""
        summary_id = str(uuid.uuid4())
        
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                """
                INSERT INTO summaries
                (id, conversation_id, summary)
                VALUES (?, ?, ?)
                """,
                (
                    summary_id,
                    summary_data["conversation_id"],
                    summary_data["summary"]
                )
            )
            conn.commit()
            
            return {"id": summary_id, **summary_data}
    
    def list_messages(self, conversation_id, page=1, limit=50):
        """List messages in a conversation."""
        offset = (page - 1) * limit
        
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT * FROM messages 
                WHERE conversation_id = ? 
                ORDER BY timestamp ASC
                LIMIT ? OFFSET ?
                """,
                (conversation_id, limit, offset)
            )
            
            rows = cursor.fetchall()
            messages = [dict(row) for row in rows]
            
            return messages
    
    def create_message(self, message_data):
        """Create a new message."""
        message_id = str(uuid.uuid4())
        
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                """
                INSERT INTO messages 
                (id, conversation_id, role, content)
                VALUES (?, ?, ?, ?)
                """,
                (
                    message_id,
                    message_data["conversation_id"],
                    message_data["role"],
                    message_data["content"]
                )
            )
            
            # Update the conversation's updated_at timestamp
            now = datetime.now().isoformat()
            cursor.execute(
                """
                UPDATE conversations
                SET updated_at = ?
                WHERE id = ?
                """,
                (now, message_data["conversation_id"])
            )
            
            conn.commit()
            
            return {"id": message_id, **message_data}

# Singleton instance
_db_manager_instance = None

def get_db_manager():
    """Get the singleton database manager instance."""
    global _db_manager_instance
    if _db_manager_instance is None:
        _db_manager_instance = DatabaseManager()
    return _db_manager_instance

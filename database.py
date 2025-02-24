import sqlite3
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_name=r"chat_history.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()

        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS chat_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,   -- شناسه منحصر به فرد خلاصه چت
                timestamp DATETIME,                      -- زمان ثبت خلاصه چت
                summary TEXT,                            -- متن خلاصه چت
                chat_history TEXT,                       -- سابقه کامل مکالمه
                model_used TEXT,                         -- نام مدل استفاده‌شده در چت
                token_count INT,                         -- تعداد توکن‌های مصرف‌شده در کل مکالمه
                user_id TEXT                             -- شناسه کاربر مربوط به چت
            )
            '''
        )

        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,     -- شناسه کاربر (مثلاً ایمیل یا شناسه یکتا)
                created_at DATETIME      -- زمان ثبت کاربر
            )
            '''
        )

        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,                -- شناسه یکتا برای عامل
                creator_id TEXT,                    -- شناسه کاربری که عامل را ایجاد کرده است
                name TEXT,                          -- نام عامل
                description TEXT,                   -- توضیحات درباره عامل
                llm_model TEXT,                     -- نام مدل زبانی مورد استفاده
                instruction_prompt TEXT,            -- دستورالعمل اولیه برای راه‌اندازی عامل
                response_style TEXT,                -- سبک پاسخ‌دهی (مثلاً رسمی یا محاوره‌ای)
                creativity REAL,                    -- میزان خلاقیت (تنظیم دما برای تولید پاسخ)
                response_length TEXT,               -- طول پاسخ (مثلاً کوتاه یا بلند)
                welcome_message TEXT,               -- پیام خوشامدگویی برای شروع مکالمه
                language TEXT,                      -- زبان عامل
                restricted_words TEXT,              -- کلمات محدود (ذخیره شده به صورت رشته‌ای با جداکننده کاما)
                resources TEXT,                     -- منابع مرتبط (ذخیره شده به صورت رشته‌ای با جداکننده کاما)
                created_at DATETIME,                -- زمان ایجاد عامل
                updated_at DATETIME                 -- زمان آخرین بروزرسانی عامل
            )
            '''
        )
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,            -- شناسه یکتا برای مکالمه
                user_id TEXT,                   -- شناسه کاربر مربوط به این مکالمه
                agent_id TEXT,                  -- شناسه عامل (چت‌بات) مربوطه
                chatbot_name TEXT,              -- نام چت‌بات
                model_name TEXT,                -- نام مدل زبانی مورد استفاده
                temperature REAL,               -- میزان دما (تنظیم خلاقیت در تولید پاسخ)
                title TEXT,                     -- عنوان مکالمه
                created_at DATETIME,            -- زمان شروع مکالمه
                updated_at DATETIME,            -- زمان آخرین به‌روزرسانی مکالمه
                last_message_at DATETIME        -- زمان ثبت آخرین پیام در مکالمه
            )
            '''
        )

        cursor.execute("PRAGMA table_info(conversations)")
        columns_info = cursor.fetchall()
        existing_columns = [col[1] for col in columns_info]
        if "chatbot_name" not in existing_columns:
            cursor.execute("ALTER TABLE conversations ADD COLUMN chatbot_name TEXT")
            self.conn.commit()

        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,            -- شناسه یکتا برای پیام
                conversation_id TEXT,           -- شناسه مکالمه مربوط به پیام
                role TEXT,                      -- نقش فرستنده (مثلاً "user" یا "assistant")
                content TEXT,                   -- محتوای پیام
                tokens_used INTEGER,            -- تعداد توکن‌های مصرف‌شده در این پیام
                created_at DATETIME,            -- زمان ارسال پیام
                file_ids TEXT                   -- شناسه‌های فایل‌های ضمیمه (ذخیره شده به صورت رشته‌ای با جداکننده کاما)
            )
            '''
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
                '''INSERT INTO agents (id, creator_id, name, description, llm_model, instruction_prompt, response_style, creativity, 
                                    response_length, welcome_message, language, restricted_words, resources, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (agent_data["id"], agent_data["creator_id"], agent_data["name"], agent_data["description"],
                agent_data["llm_model"], agent_data["instruction_prompt"], agent_data["response_style"],
                agent_data["creativity"], agent_data["response_length"], agent_data["welcome_message"],
                agent_data["language"], ",".join(agent_data.get("restricted_words", [])),
                ",".join(agent_data.get("resources", [])), now, now)
            )
            self.conn.commit()
            agent_data["created_at"] = now.isoformat()
            agent_data["updated_at"] = now.isoformat()
            return agent_data
        except Exception as e:
            print("Error creating agent:", e)
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
            print("Error updating agent:", e)
            return None

    def get_agent(self, agent_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM agents WHERE id=?", (agent_id,))
        row = cursor.fetchone()
        if row:
            columns = [desc[0] for desc in cursor.description]
            agent = dict(zip(columns, row))
            if agent.get("restricted_words"):
                agent["restricted_words"] = agent["restricted_words"].split(",")
            else:
                agent["restricted_words"] = []
            if agent.get("resources"):
                agent["resources"] = agent["resources"].split(",")
            else:
                agent["resources"] = []
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
        conversations = [dict(zip(columns, row)) for row in rows]
        return conversations

    def create_conversation(self, conversation_data):
        cursor = self.conn.cursor()
        now = datetime.now()
        conversation_id = conversation_data.get("id")
        cursor.execute(
            '''INSERT INTO conversations (id, user_id, agent_id, chatbot_name, model_name, temperature, title, created_at, updated_at, last_message_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (conversation_id,
             conversation_data.get("user_id"),
             conversation_data.get("agent_id"),
             conversation_data.get("chatbot_name"),
             conversation_data.get("model_name"),
             conversation_data.get("temperature"),
             conversation_data.get("title"),
             now, now, now)
        )
        self.conn.commit()
        conversation_data["created_at"] = now.isoformat()
        conversation_data["updated_at"] = now.isoformat()
        conversation_data["last_message_at"] = now.isoformat()
        return conversation_data

    def save_summary(self, summary_data):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                '''INSERT INTO chat_summaries 
                  (timestamp, summary, chat_history, model_used, token_count, user_id)
                  VALUES (?, ?, ?, ?, ?, ?)''',
                (datetime.now(), summary_data['summary'], summary_data['chat_history'],
                summary_data['model'], summary_data['tokens'], summary_data['user_id'])
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Database error: {str(e)}")
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
        messages = [dict(zip(columns, row)) for row in rows]
        return messages

    def create_message(self, message_data):
        cursor = self.conn.cursor()
        now = datetime.now()
        message_id = message_data.get("id")
        file_ids = ",".join(message_data.get("file_ids", []))
        cursor.execute(
            '''INSERT INTO messages (id, conversation_id, role, content, tokens_used, created_at, file_ids)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (message_id,
             message_data.get("conversation_id"),
             message_data.get("role"),
             message_data.get("content"),
             message_data.get("tokens_used"),
             now,
             file_ids)
        )
        self.conn.commit()
        message_data["created_at"] = now.isoformat()
        return message_data
# src/db/db_manager.py
import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime


class DBManager:
    """数据库管理器"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.db_dir = Path(__file__).parent.parent.parent / 'data' / 'db'
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.db_dir / 'chat_history.db'
        self._init_db()

    def _init_db(self) -> None:
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建对话会话表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            character_id TEXT NOT NULL,
            session_name TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
        ''')
        
        # 创建消息表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            FOREIGN KEY (session_id) REFERENCES chat_sessions (id) ON DELETE CASCADE
        )
        ''')
        
        # 创建摘要表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL,
            FOREIGN KEY (session_id) REFERENCES chat_sessions (id) ON DELETE CASCADE
        )
        ''')
        
        conn.commit()
        conn.close()

    def create_session(self, character_id: str, session_name: Optional[str] = None) -> int:
        """创建新的聊天会话"""
        if not session_name:
            now = datetime.now()
            session_name = f"{character_id}_{now.strftime('%Y%m%d_%H%M%S')}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now_str = datetime.now().isoformat()
        
        cursor.execute(
            "INSERT INTO chat_sessions (character_id, session_name, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (character_id, session_name, now_str, now_str)
        )
        
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return session_id

    def add_message(self, session_id: int, role: str, content: str) -> int:
        """添加消息到会话"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now_str = datetime.now().isoformat()
        
        cursor.execute(
            "INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
            (session_id, role, content, now_str)
        )
        
        message_id = cursor.lastrowid
        
        # 更新会话的更新时间
        cursor.execute(
            "UPDATE chat_sessions SET updated_at = ? WHERE id = ?",
            (now_str, session_id)
        )
        
        conn.commit()
        conn.close()
        
        return message_id

    def get_session_messages(self, session_id: int) -> List[Dict[str, str]]:
        """获取会话的所有消息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT role, content FROM messages WHERE session_id = ? ORDER BY timestamp",
            (session_id,)
        )
        
        messages = [{"role": role, "content": content} for role, content in cursor.fetchall()]
        conn.close()
        
        return messages

    def get_recent_sessions(self, limit: int = 10) -> List[Dict]:
        """获取最近的会话列表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT id, character_id, session_name, created_at, updated_at 
            FROM chat_sessions 
            ORDER BY updated_at DESC 
            LIMIT ?
            """,
            (limit,)
        )
        
        sessions = []
        for row in cursor.fetchall():
            session_id, character_id, session_name, created_at, updated_at = row
            
            # 获取消息数量
            cursor.execute("SELECT COUNT(*) FROM messages WHERE session_id = ?", (session_id,))
            message_count = cursor.fetchone()[0]
            
            sessions.append({
                "id": session_id,
                "character_id": character_id,
                "name": session_name,
                "created_at": created_at,
                "updated_at": updated_at,
                "message_count": message_count
            })
        
        conn.close()
        return sessions

    def delete_session(self, session_id: int) -> bool:
        """删除会话及其所有消息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            cursor.execute("DELETE FROM summaries WHERE session_id = ?", (session_id,))
            cursor.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
            conn.commit()
            success = True
        except Exception:
            conn.rollback()
            success = False
        finally:
            conn.close()
        
        return success

    def add_summary(self, session_id: int, content: str) -> int:
        """添加会话摘要"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now_str = datetime.now().isoformat()
        
        cursor.execute(
            "INSERT INTO summaries (session_id, content, created_at) VALUES (?, ?, ?)",
            (session_id, content, now_str)
        )
        
        summary_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return summary_id

    def get_latest_summary(self, session_id: int) -> Optional[str]:
        """获取会话的最新摘要"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT content FROM summaries 
            WHERE session_id = ? 
            ORDER BY created_at DESC 
            LIMIT 1
            """,
            (session_id,)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None


# 创建全局数据库管理器实例
db_manager = DBManager()

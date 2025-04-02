# src/models/conversation.py
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from src.db.db_manager import db_manager


@dataclass
class Conversation:
    """对话管理类"""
    character_id: str = ""
    session_id: Optional[int] = None
    messages: List[Dict[str, str]] = field(default_factory=list)
    context_hints: List[str] = field(default_factory=list)
    use_db: bool = True  # 是否使用数据库

    def __post_init__(self):
        """初始化后的处理"""
        if self.use_db and self.character_id and not self.session_id:
            # 如果未提供会话ID，创建新会话
            self.session_id = db_manager.create_session(self.character_id)
            # 从数据库加载消息
            self.messages = db_manager.get_session_messages(self.session_id)

    def add_message(self, role: str, content: str) -> None:
        """添加新消息"""
        message = {
            "role": role,
            "content": content
        }
        self.messages.append(message)
        
        # 如果启用数据库，保存到数据库
        if self.use_db and self.session_id:
            db_manager.add_message(self.session_id, role, content)

    def add_context_hint(self, hint: str) -> None:
        """添加上下文提示"""
        self.context_hints.append(hint)

    def clear_context_hints(self) -> None:
        """清除上下文提示"""
        self.context_hints.clear()

    def get_messages(self) -> List[Dict[str, str]]:
        """获取原始消息列表"""
        return self.messages.copy()

    def get_messages_with_context(self) -> List[Dict[str, str]]:
        """获取包含上下文提示的消息列表"""
        if not self.context_hints:
            return self.messages.copy()

        messages = self.messages.copy()
        insert_pos = len(messages) - 1 if messages else 0

        messages.insert(insert_pos, {
            "role": "system",
            "content": "\n".join(self.context_hints)
        })

        return messages
    
    def clear_history(self) -> None:
        """清除对话历史但保留系统提示"""
        # 保留系统提示消息
        system_messages = [msg for msg in self.messages if msg["role"] == "system"]
        self.messages = system_messages
        
        # 如果启用数据库，创建新会话
        if self.use_db and self.character_id:
            old_session_id = self.session_id
            self.session_id = db_manager.create_session(self.character_id)
            
            # 复制系统提示到新会话
            for msg in system_messages:
                db_manager.add_message(self.session_id, msg["role"], msg["content"])
    
    def load_session(self, session_id: int) -> None:
        """加载指定的对话会话"""
        if not self.use_db:
            return
            
        self.session_id = session_id
        self.messages = db_manager.get_session_messages(session_id)
# src/models/conversation.py
from typing import List, Dict
from dataclasses import dataclass, field


@dataclass
class Conversation:
    """对话管理类"""
    messages: List[Dict[str, str]] = field(default_factory=list)
    context_hints: List[str] = field(default_factory=list)

    def add_message(self, role: str, content: str) -> None:
        """添加新消息"""
        self.messages.append({
            "role": role,
            "content": content
        })

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
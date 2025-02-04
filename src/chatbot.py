# src/chatbot/chatbot.py
from typing import Optional

from character.character import Character
from config.config_manager import config_manager
from models.conversation import Conversation
from services.chat_service import get_selected_bot


class ChatBot:
    """聊天机器人主类"""

    def __init__(self, character_id: str = "li_ming"):
        self.chatbot = get_selected_bot()
        self.conversation = Conversation()
        self.load_character(character_id)

    def load_character(self, character_id: str) -> None:
        """加载新角色"""
        self.character = Character(character_id)
        self.current_character_id = character_id
        self._initialize_conversation()

    def _initialize_conversation(self) -> None:
        """初始化对话"""
        self.conversation = Conversation()
        system_prompt = self.character.get_system_prompt()
        self.conversation.add_message("system", system_prompt)

    async def chat(self, user_input: str) -> Optional[str]:
        """处理用户输入并返回响应"""
        try:
            # 获取上下文提示
            context_hint = self.character.get_context_hints(user_input)
            if context_hint:
                self.conversation.add_context_hint(context_hint)

            # 添加用户输入
            self.conversation.add_message("user", user_input)

            # 获取完整的对话历史
            messages = self.conversation.get_messages_with_context()

            # 获取配置参数
            max_tokens = int(config_manager.get_config_value('MAX_TOKENS', '40000'))

            # 发送请求获取响应
            response = await self.chatbot.send_message(
                messages=messages,
                temperature=self.chatbot.get_temperature(),
                max_tokens=max_tokens
            )

            # 保存 AI 响应
            self.conversation.add_message("assistant", response)

            # 清理上下文提示
            self.conversation.clear_context_hints()

            return response

        except Exception as e:
            raise ChatBotError(f"Chat error: {str(e)}")

    def clear_history(self) -> None:
        """清除对话历史"""
        self._initialize_conversation()

    def get_current_character(self) -> str:
        """获取当前角色ID"""
        return self.current_character_id

    def get_conversation_history(self) -> list:
        """获取对话历史"""
        return self.conversation.get_messages()


class ChatBotError(Exception):
    """聊天机器人错误"""
    pass
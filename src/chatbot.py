# src/chatbot/chatbot.py
from typing import Optional, List, Dict

from src.character.character import Character
from src.config.config_manager import config_manager
from src.models.conversation import Conversation
from src.services.chat_service import ChatService
from src.db.db_manager import db_manager
from src.vector.vector_store import vector_store
from src.summarizer.conversation_summarizer import conversation_summarizer


class ChatBot:
    """聊天机器人主类"""

    def __init__(self, character_id: str = "li_ming"):
        self.chat_service = ChatService()
        self.conversation = None
        self.load_character(character_id)

    def load_character(self, character_id: str) -> None:
        """加载新角色"""
        self.character = Character(character_id)
        self.current_character_id = character_id
        self._initialize_conversation()

    def _initialize_conversation(self) -> None:
        """初始化对话"""
        self.conversation = Conversation(character_id=self.current_character_id)
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
            
            # 如果启用了向量存储，保存用户消息到向量存储
            try:
                if self.conversation.session_id:
                    vector_store.add_user_message(
                        message=user_input,
                        session_id=self.conversation.session_id
                    )
            except Exception as e:
                print(f"保存用户消息到向量存储失败: {str(e)}")

            # 获取完整的对话历史
            messages = self.conversation.get_messages_with_context()

            # 获取配置参数
            temperature = float(config_manager.get_config_value('TEMPERATURE', '0.7'))
            max_tokens = int(config_manager.get_config_value('MAX_TOKENS', '2000'))

            # 发送请求获取响应
            response = await self.chat_service.send_message(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            # 保存 AI 响应
            self.conversation.add_message("assistant", response)
            
            # 每隔一定次数的对话后生成摘要
            await self._maybe_generate_summary()

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

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """获取对话历史"""
        return self.conversation.get_messages()
        
    def get_session_id(self) -> Optional[int]:
        """获取当前会话ID"""
        return self.conversation.session_id if self.conversation else None
        
    def load_session(self, session_id: int) -> None:
        """加载指定的会话"""
        if not self.conversation:
            self.conversation = Conversation(character_id=self.current_character_id)
        
        self.conversation.load_session(session_id)
        
    def get_recent_sessions(self, limit: int = 10) -> List[Dict]:
        """获取最近的会话列表"""
        return db_manager.get_recent_sessions(limit=limit)
        
    async def _maybe_generate_summary(self) -> None:
        """在适当时机生成对话摘要"""
        # 如果没有会话ID或消息少于一定数量，则跳过
        if not self.conversation or not self.conversation.session_id:
            return
            
        # 获取对话历史
        history = self.conversation.get_messages()
        
        # 检查非系统消息的数量
        non_system_messages = [msg for msg in history if msg["role"] != "system"]
        if len(non_system_messages) % 10 != 0:  # 每10条非系统消息生成一次摘要
            return
            
        # 生成摘要
        summary = await conversation_summarizer.generate_summary(
            session_id=self.conversation.session_id,
            conversation_history=history
        )
        
        return summary
        
    async def generate_summary(self) -> Optional[str]:
        """手动生成对话摘要"""
        if not self.conversation or not self.conversation.session_id:
            return None
            
        return await conversation_summarizer.generate_summary(
            session_id=self.conversation.session_id,
            conversation_history=self.conversation.get_messages()
        )
        
    def get_latest_summary(self) -> Optional[str]:
        """获取最新的对话摘要"""
        if not self.conversation or not self.conversation.session_id:
            return None
            
        return db_manager.get_latest_summary(self.conversation.session_id)


class ChatBotError(Exception):
    """聊天机器人错误"""
    pass
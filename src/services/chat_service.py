# src/services/chat_service.py
from typing import List, Dict, Optional
from zhipuai import ZhipuAI
from config.config_manager import config_manager


class ChatService:
    """AI 聊天服务"""

    def __init__(self):
        self.api_key = config_manager.get_api_key()
        self.client = ZhipuAI(api_key=self.api_key)
        self.model = config_manager.get_config_value('MODEL_NAME', 'charglm-4')

    async def send_message(
            self,
            messages: List[Dict[str, str]],
            temperature: float = 0.7,
            max_tokens: Optional[int] = None
    ) -> str:
        """
        发送消息到 AI 服务

        Args:
            messages: 消息历史列表
            temperature: 温度参数
            max_tokens: 最大标记数

        Returns:
            AI 的响应文本

        Raises:
            ChatServiceError: 当 API 调用失败时
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content

        except Exception as e:
            raise ChatServiceError(f"API call failed: {str(e)}")


class ChatServiceError(Exception):
    """聊天服务错误"""
    pass
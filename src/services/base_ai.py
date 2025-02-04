from typing import List, Dict, Optional


class ChatServiceError(Exception):
    """聊天服务错误"""
    pass


class AbstractChatBot:
    """AI 聊天服务"""

    def __init__(self):
        self.client = self.get_client()
        self.model = self.get_model_name()

    def get_client(self):
        raise NotImplementedError()

    def get_model_name(self) -> str:
        raise NotImplementedError()

    def get_temperature(self) -> float:
        return 1.0

    async def send_message(
            self,
            messages: List[Dict[str, str]],
            temperature: float = 1.3,
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

# src/services/chat_service.py
from zhipuai import ZhipuAI
from config.config_manager import config_manager
from services.base_ai import AbstractChatBot


class Charglm(AbstractChatBot):
    """AI 聊天服务"""

    def get_client(self):
        api_key = config_manager.get_api_key()
        return ZhipuAI(api_key=api_key)

    def get_model_name(self) -> str:
        return config_manager.get_config_value('MODEL_NAME', 'charglm-4')
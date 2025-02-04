import openai
from services.base_ai import AbstractChatBot


class Deepseekbot(AbstractChatBot):
    def get_client(self):
        client = openai.OpenAI(
            base_url="http://localhost:11434/v1",
            api_key="nokeyneeded")
        return client

    def get_model_name(self) -> str:
        return "deepseek-r1:14b"

    def get_temperature(self) -> float:
        return 1.3
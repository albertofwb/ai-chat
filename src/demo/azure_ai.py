import os
from openai import AzureOpenAI
from config.config_manager import config_manager

# 设置环境变量
os.environ["AZURE_OPENAI_ENDPOINT"] = config_manager.get_config_value("AZURE_OPENAI_ENDPOINT")
os.environ["AZURE_OPENAI_API_KEY"] = config_manager.get_config_value("AZURE_OPENAI_API_KEY")
API_VERSION = config_manager.get_config_value('AZURE_OPENAI_API_KEY')
model_name = config_manager.get_config_value('AZURE_MODEL_NAME')

client = AzureOpenAI(
    api_version=API_VERSION,
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
)


def chat_with_gpt4(messages):
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def create_text_with_openai(user_input: str):
    messages = [
        {"role": "system",
         "content": user_input}
    ]

    while True:
        # 添加用户输入到消息历史
        messages.append({"role": "user", "content": user_input})
        # 获取AI响应
        response = chat_with_gpt4(messages)
        yield response
        messages.append({"role": "assistant", "content": messages})


def demo():
    message_text = [{"role": "system", "content": "You are an AI assistant that helps people find information."},
                    {"role": "user", "content": "长城有多长？"}]

    chat_completion = client.chat.completions.create(
        model="gpt35_0613",  # 这个地方是要你设定的deployment_name，不是具体的模型名称，也可以是基于gpt4创建的部署名
        messages=message_text
    )

    print(chat_completion.choices[0].message.content)


if __name__ == '__main__':
    demo()

from dotenv import load_dotenv
import os


def get_api_key():
    # 加载 .env 文件中的环境变量
    load_dotenv()

    # 获取 API_KEY
    api_key = os.getenv('API_KEY')

    if not api_key:
        raise ValueError("API_KEY not found in .env file")

    return api_key


if __name__ == "__main__":
    try:
        api_key = get_api_key()
        print(f"Successfully loaded API key: {api_key}")
    except Exception as e:
        print(f"Error: {e}")
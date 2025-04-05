# src/config/config_manager.py
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class ConfigManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.config_dir = self._get_config_dir()
        self._load_env()

    @staticmethod
    def _get_config_dir() -> Path:
        """获取配置文件目录"""
        # 获取当前文件所在目录的父目录的父目录（项目根目录）
        root_dir = Path(__file__).parent.parent.parent
        return root_dir / 'config'

    def _load_env(self) -> None:
        """加载环境变量"""
        env_path = self.config_dir / '.env'
        if not env_path.exists():
            with open(env_path, 'w') as fp:
                fp.write('''
API_KEY=xxx
MODEL_NAME=charglm-4
TEMPERATURE=0.7
MAX_TOKENS=2000

# Paths
CHARACTERS_DIR=characters
''')
            raise FileNotFoundError(f"please enter API_KEY at {env_path}")

        load_dotenv(env_path)

    def get_api_key(self) -> str:
        """获取 API key"""
        api_key = os.getenv('API_KEY')
        if not api_key:
            raise ValueError("API_KEY not found in environment variables")
        return api_key

    def get_model_name(self) -> str:
        """获取模型名称"""
        return os.getenv('MODEL_NAME', 'charglm-4')

    def get_tts_api_key(self) -> str:
        """获取 TTS API key"""
        return os.getenv('TTS_API_KEY')

    def get_character_dir(self) -> Path:
        """获取角色配置目录"""
        return self.config_dir / 'characters'

    def get_config_value(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """获取指定配置项的值"""
        return os.getenv(key, default)


# 创建全局配置管理器实例
config_manager = ConfigManager()

if __name__ == '__main__':
    print(config_manager.get_tts_api_key())
# src/tts/voice_service.py
import os
import asyncio
import hashlib
from pathlib import Path
from typing import Optional

# 添加到 requirements.txt:
# edge-tts


class VoiceService:
    """文本到语音服务"""
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
        self.voice_cache_dir = Path(__file__).parent.parent.parent / 'data'
        self.voice_cache_dir.mkdir(exist_ok=True)
        
        # 默认语音配置
        self.default_voice = "zh-CN-XiaomoNeural"  # 中文女声
        
        # 特定角色的语音映射
        self.character_voice_map = {
            "li_ming": "zh-CN-YunjianNeural",  # 中文男声
            "wang_biao": "zh-CN-YunxiNeural",   # 中文男声(年轻)
            "zhang_ning": "zh-CN-XiaohanNeural", # 中文女声
        }
        
        # 尝试导入edge-tts
        try:
            import edge_tts
            self.edge_tts = edge_tts
            self.tts_available = True
        except ImportError:
            print("TTS服务需要安装 edge-tts 模块，请运行: pip install edge-tts")
            self.tts_available = False
    
    def get_voice_for_character(self, character_id: str) -> str:
        """获取角色对应的语音"""
        return self.character_voice_map.get(character_id, self.default_voice)
    
    async def text_to_speech(self, text: str, character_id: Optional[str] = None) -> Optional[str]:
        """将文本转换为语音，返回音频文件路径"""
        if not self.tts_available:
            print("TTS服务不可用")
            return None
            
        # 获取对应的语音
        voice = self.get_voice_for_character(character_id) if character_id else self.default_voice
        
        # 生成缓存键
        cache_key = hashlib.md5(f"{text}_{voice}".encode()).hexdigest()
        output_file = self.voice_cache_dir / f"{cache_key}_{voice}.wav"
        
        # 如果缓存存在，直接返回
        if output_file.exists():
            return str(output_file)
        
        try:
            # 使用edge-tts生成语音
            communicate = self.edge_tts.Communicate(text, voice)
            await communicate.save(str(output_file))
            return str(output_file)
        except Exception as e:
            print(f"生成语音失败: {str(e)}")
            return None

    async def generate_voice(self, text: str, character_id: Optional[str] = None) -> Optional[str]:
        """生成语音并返回文件路径"""
        return await self.text_to_speech(text, character_id)
        

# 创建全局语音服务实例
voice_service = VoiceService()


if __name__ == "__main__":
    # 测试
    async def test():
        result = await voice_service.text_to_speech("这是一条测试语音消息。")
        print(f"生成的语音文件: {result}")
    
    asyncio.run(test())

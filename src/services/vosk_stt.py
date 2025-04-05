import os

import vosk
import pyaudio
import json


class ChineseVoiceRecognizer:
    def __init__(self):
        """初始化语音检测器"""
        # 加载中文模型
        vosk.SetLogLevel(-1)  # 禁用日志
        script_dir = os.path.dirname(__file__)
        model_name = "vosk-model-cn-0.22"
        model_path = os.path.join(script_dir, model_name)

        # 检查模型目录是否存在
        if os.path.exists(model_path) and os.path.isdir(model_path):
            print(f"使用模型路径: {model_path}")
            self.model = vosk.Model(model_path)
            self.recognizer = vosk.KaldiRecognizer(self.model, 16000)
        else:
            raise FileNotFoundError(f"模型目录不存在: {model_path}")

        # 音频设置
        self.audio = pyaudio.PyAudio()

    def get_speech_text(self) -> str:
        """开始录音并等待说话结束"""
        stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=8000
        )
        stream.start_stream()

        print("开始说话...")
        recognized_text = ""

        try:
            while True:
                data = stream.read(4000)
                if len(data) == 0:
                    break

                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get("text", "")
                    if text:
                        recognized_text = text
                        print(f"识别到的文本: {text}")
                        break
        finally:
            stream.stop_stream()
            stream.close()

        return recognized_text

    def __del__(self):
        if hasattr(self, "audio"):
            self.audio.terminate()
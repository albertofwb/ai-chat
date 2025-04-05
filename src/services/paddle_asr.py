import paddlespeech.cli.asr as asr


class ChineseVoiceRecognizer:
    def __init__(self):
        self.asr_engine = asr.ASRExecutor()

    def get_speech_text(self) -> str:
        """开始录音并识别语音"""
        result = self.asr_engine.recognize_mic(
            model='conformer_wenetspeech',  # 使用中文模型
            lang='zh',
            sample_rate=16000,
            force_yes=True
        )
        print(f"识别到的文本: {result}")
        return result

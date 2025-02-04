import azure.cognitiveservices.speech as speechsdk
import time


class MSVoiceDetector:
    def __init__(self, speech_key, service_region):
        """
        初始化语音检测器
        """
        self.speech_config = speechsdk.SpeechConfig(
            subscription=speech_key,
            region=service_region
        )
        self.speech_config.speech_recognition_language = "zh-CN"

        # 创建音频配置
        self.audio_input_config = speechsdk.audio.AudioConfig(
            use_default_microphone=True
        )

        # 创建语音识别器
        self.speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config,
            audio_config=self.audio_input_config,
        )

    def get_speech_text(self):
        """开始录音并等待说话结束"""
        # 用于同步的事件
        done = False
        recognized_text = ""

        def handle_result(evt):
            """处理识别结果"""
            nonlocal done, recognized_text
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                print(f"识别到的文本: {evt.result.text}")
                recognized_text = evt.result.text
                done = True

        # 设置回调
        self.speech_recognizer.recognized.connect(handle_result)
        self.speech_recognizer.session_stopped.connect(lambda evt: setattr(done, 'value', True))

        # 开始识别
        self.speech_recognizer.start_continuous_recognition()

        # 等待识别结束
        while not done:
            time.sleep(0.1)

        # 停止识别
        self.speech_recognizer.stop_continuous_recognition()
        return recognized_text


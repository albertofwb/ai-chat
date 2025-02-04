from services.ms_voice_detector import MSVoiceDetector
from services.speech_assistant import SpeechAssistant
from config.config_manager import config_manager


def get_voice_detector() -> MSVoiceDetector:

    speech_key = config_manager.get_config_value('speech_key')
    service_region = config_manager.get_config_value("service_region")

    detector = MSVoiceDetector(speech_key, service_region)
    return detector



def get_speech_instance() -> SpeechAssistant:
    speech_key = config_manager.get_config_value('speech_key')
    service_region = config_manager.get_config_value("service_region")

    return SpeechAssistant(
            speech_key,
            service_region,
            "data",
            "zh-CN-XiaomoNeural")
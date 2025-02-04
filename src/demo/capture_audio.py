from datetime import datetime
from demo.voice_recorder import MSVoiceDetector
import wave

def main():
    # 替换为你的密钥和区域
    speech_key = "6a45ee083dbc4df6973907474260d7fa"
    service_region = "eastus"
    # 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"recording_{timestamp}.wav"
    detector = MSVoiceDetector(speech_key, service_region)

    try:
        while True:
            input("按回车开始录音...")

            # 开始录音和识别
            text = detector.start_recording()
            print(f"音频已保存至: {filename}")
            response = input("继续录音? (y/n): ")
            if response.lower() != 'y':
                break

    except KeyboardInterrupt:
        print("\n录音结束")


if __name__ == "__main__":
    main()
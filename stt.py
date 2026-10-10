import tempfile
import wave
import os

import numpy as np
import sounddevice as sd
import torch
import whisper


from config import (
    WHISPER_MODEL,
    WHISPER_LANGUAGE,
)


# ============================================================
# FFmpeg
# ============================================================

FFMPEG_BIN = r"D:\OTHERS\AI\ffmpeg\bin"

# 加入当前 Python 进程的 PATH
os.environ["PATH"] = (
    FFMPEG_BIN
    + os.pathsep
    + os.environ.get("PATH", "")
)


class SpeechToText:

    def __init__(self):

        print("正在加载 Whisper...")

        # 自动判断 GPU / CPU
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        print(f"使用设备: {self.device}")

        # 本地 Whisper 模型
        self.model = whisper.load_model(
            r"D:\OTHERS\AI\models\medium.pt",
            device=self.device
        )

        print("Whisper 加载完成")

    def record(self):

        print()
        print("=" * 50)
        print("按 Enter 开始录音")
        input()

        print("正在录音……再次按 Enter 停止")

        recording = []

        stream = sd.InputStream(
            samplerate=16000,
            channels=1,
            dtype="float32",
            callback=lambda indata, frames, time, status:
                recording.append(indata.copy())
        )

        stream.start()

        input()

        stream.stop()
        stream.close()

        if not recording:
            return ""

        audio = np.concatenate(recording, axis=0)
        audio = np.clip(audio, -1, 1)

        temp_file = tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False
        )

        temp_file.close()

        with wave.open(temp_file.name, "wb") as wf:

            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)

            pcm = (audio * 32767).astype(np.int16)

            wf.writeframes(pcm.tobytes())

        return temp_file.name

    def transcribe(self, wav_path):

        print("正在使用 Whisper 识别...")

        # CPU 时关闭 fp16
        result = self.model.transcribe(
            wav_path,
            language=WHISPER_LANGUAGE,
            beam_size=5,
            fp16=(self.device == "cuda")
        )

        return result["text"].strip()
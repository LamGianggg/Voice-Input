# thuam_1phim.py - Có tăng âm lượng
import sounddevice as sd
import numpy as np
import wave
from datetime import datetime
from pynput import keyboard
import os

# === Cấu hình ===
SAMPLE_RATE = 44100
CHANNELS = 1
OUTPUT_DIR = "raw_audio"
GAIN = 10.0              # Hệ số khuếch đại (1 = giữ nguyên, 2 = gấp đôi, 3 = gấp ba)
MAX_AMPLITUDE = 32767   # Giới hạn để tránh bị vỡ tiếng (clipping)

os.makedirs(OUTPUT_DIR, exist_ok=True)

recording = False
audio_frames = []
current_file = None

def start():
    global recording, audio_frames, current_file
    if recording:
        return
    recording = True
    audio_frames = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"thuam_{timestamp}.wav"
    current_file = os.path.join(OUTPUT_DIR, filename)
    print(f"🔴 ĐANG GHI... (độ khuếch đại x{GAIN}) Nhấn 's' để dừng. File: {current_file}")

def stop():
    global recording
    if not recording:
        return
    recording = False
    if audio_frames:
        audio_data = np.concatenate(audio_frames, axis=0)
        # Nhân với hệ số GAIN
        audio_data = audio_data * GAIN
        # Giới hạn trong khoảng -1..1 để tránh bị vỡ
        audio_data = np.clip(audio_data, -1.0, 1.0)
        # Chuyển sang int16
        audio_int16 = (audio_data * MAX_AMPLITUDE).astype(np.int16)
        with wave.open(current_file, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio_int16.tobytes())
        print(f"✅ Đã lưu: {current_file}")
    else:
        print("⚠️ Không có dữ liệu âm thanh.")

def on_press(key):
    try:
        if key.char == 'r':
            start()
        elif key.char == 's':
            stop()
        elif key.char == 'q':
            print("👋 Thoát chương trình.")
            return False
    except AttributeError:
        pass
    return True

def audio_callback(indata, frames, time, status):
    if recording:
        audio_frames.append(indata.copy())

stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, callback=audio_callback)
stream.start()

print("🎤 Chương trình ghi âm – Nhấn 'r' để ghi, 's' để dừng, 'q' để thoát.")
print(f"🔊 Hệ số khuếch đại hiện tại: {GAIN}x")
with keyboard.Listener(on_press=on_press) as listener:
    listener.join()

stream.stop()
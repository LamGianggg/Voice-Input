# recorder_ui.py
import sys
import os
import sounddevice as sd
import numpy as np
import wave
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                                QHBoxLayout, QPushButton, QLabel, QSlider, QMessageBox)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont


class RecorderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NCKH - Ghi âm giọng nói")
        self.setFixedSize(500, 300)

        # Cấu hình ghi âm
        self.sample_rate = 44100
        self.channels = 1
        self.output_dir = "raw_audio"
        os.makedirs(self.output_dir, exist_ok=True)

        self.is_recording = False
        self.audio_frames = []
        self.current_file = None
        self.stream = None
        self.gain = 2.0  # Hệ số khuếch đại mặc định

        # Tạo giao diện
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Label trạng thái
        self.status_label = QLabel("Sẵn sàng")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Arial", 12))
        layout.addWidget(self.status_label)

        # Label thời gian ghi
        self.time_label = QLabel("00:00")
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setFont(QFont("Monospace", 24, QFont.Bold))
        layout.addWidget(self.time_label)

        # Thanh trượt điều chỉnh gain
        gain_layout = QHBoxLayout()
        gain_layout.addWidget(QLabel("Âm lượng (gain):"))
        self.gain_slider = QSlider(Qt.Horizontal)
        self.gain_slider.setRange(10, 50)  # 1.0x -> 5.0x
        self.gain_slider.setValue(int(self.gain * 10))
        self.gain_slider.valueChanged.connect(self.change_gain)
        gain_layout.addWidget(self.gain_slider)
        self.gain_label = QLabel(f"{self.gain:.1f}x")
        gain_layout.addWidget(self.gain_label)
        layout.addLayout(gain_layout)

        # Các nút bấm
        btn_layout = QHBoxLayout()
        self.record_btn = QPushButton("🎙 Ghi âm")
        self.stop_btn = QPushButton("⏹ Dừng")
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.record_btn)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)

        # Kết nối sự kiện
        self.record_btn.clicked.connect(self.start_recording)
        self.stop_btn.clicked.connect(self.stop_recording)

        # Timer để cập nhật thời gian ghi
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.record_duration = 0

    def change_gain(self, value):
        self.gain = value / 10.0
        self.gain_label.setText(f"{self.gain:.1f}x")

    def start_recording(self):
        if self.is_recording:
            return
        self.is_recording = True
        self.audio_frames = []
        self.record_duration = 0
        self.update_time()
        self.timer.start(1000)  # cập nhật mỗi giây

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"thuam_{timestamp}.wav"
        self.current_file = os.path.join(self.output_dir, filename)

        # Mở luồng ghi âm
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            callback=self.audio_callback
        )
        self.stream.start()

        self.status_label.setText("🔴 ĐANG GHI...")
        self.record_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def audio_callback(self, indata, frames, time, status):
        if self.is_recording:
            self.audio_frames.append(indata.copy())

    def stop_recording(self):
        if not self.is_recording:
            return
        self.is_recording = False
        self.timer.stop()

        if self.stream:
            self.stream.stop()
            self.stream.close()

        if self.audio_frames:
            # Xử lý và lưu file
            audio_data = np.concatenate(self.audio_frames, axis=0)
            # Nhân gain
            audio_data = audio_data * self.gain
            # Giới hạn tránh vỡ tiếng
            audio_data = np.clip(audio_data, -1.0, 1.0)
            # Chuyển sang int16
            audio_int16 = (audio_data * 32767).astype(np.int16)

            with wave.open(self.current_file, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_int16.tobytes())

            self.status_label.setText(
                f"✅ Đã lưu: {os.path.basename(self.current_file)}")
            QMessageBox.information(
                self, "Thành công", f"Đã lưu file:\n{self.current_file}")
        else:
            self.status_label.setText("⚠️ Không có dữ liệu")
            QMessageBox.warning(
                self, "Lỗi", "Không ghi được dữ liệu âm thanh.")

        self.record_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.current_file = None

    def update_time(self):
        self.record_duration += 1
        minutes = self.record_duration // 60
        seconds = self.record_duration % 60
        self.time_label.setText(f"{minutes:02d}:{seconds:02d}")

    def closeEvent(self, event):
        if self.is_recording:
            reply = QMessageBox.question(self, "Đang ghi âm",
                                        "Bạn đang ghi âm. Bạn có muốn dừng và thoát không?",
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.stop_recording()
            else:
                event.ignore()
                return
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = RecorderApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

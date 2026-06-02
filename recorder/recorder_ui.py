# recorder_ui.py (đã sửa lỗi cú pháp)
import sys
import os
import sounddevice as sd
import numpy as np
import wave
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QPushButton, QLabel, QSlider, QMessageBox,
                               QTableWidget, QTableWidgetItem, QDialog, QHeaderView)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont

# Import module trích xuất đặc trưng
from feature_extractor import extract_features, save_features_to_csv


class RecorderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NCKH - Ghi âm và Trích xuất đặc trưng")
        self.setFixedSize(700, 400)

        self.sample_rate = 44100
        self.channels = 1
        self.output_dir = "raw_audio"
        os.makedirs(self.output_dir, exist_ok=True)

        self.is_recording = False
        self.audio_frames = []
        self.current_file = None
        self.stream = None
        self.gain = 2.0

        # Tạo giao diện
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.status_label = QLabel("Sẵn sàng")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Arial", 12))
        layout.addWidget(self.status_label)

        self.time_label = QLabel("00:00")
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setFont(QFont("Monospace", 24, QFont.Bold))
        layout.addWidget(self.time_label)

        gain_layout = QHBoxLayout()
        gain_layout.addWidget(QLabel("Âm lượng (gain):"))
        self.gain_slider = QSlider(Qt.Horizontal)
        self.gain_slider.setRange(10, 50)
        self.gain_slider.setValue(int(self.gain * 10))
        self.gain_slider.valueChanged.connect(self.change_gain)
        gain_layout.addWidget(self.gain_slider)
        self.gain_label = QLabel(f"{self.gain:.1f}x")
        gain_layout.addWidget(self.gain_label)
        layout.addLayout(gain_layout)

        btn_layout = QHBoxLayout()
        self.record_btn = QPushButton("🎙 Ghi âm")
        self.stop_btn = QPushButton("⏹ Dừng")
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.record_btn)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)

        self.view_features_btn = QPushButton("📊 Xem đặc trưng cuối")
        self.view_features_btn.setEnabled(False)
        layout.addWidget(self.view_features_btn)

        self.record_btn.clicked.connect(self.start_recording)
        self.stop_btn.clicked.connect(self.stop_recording)
        self.view_features_btn.clicked.connect(self.show_last_features)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.record_duration = 0
        self.last_features_csv = None

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
        self.timer.start(1000)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"thuam_{timestamp}.wav"
        self.current_file = os.path.join(self.output_dir, filename)

        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            callback=self.audio_callback
        )
        self.stream.start()

        self.status_label.setText("🔴 ĐANG GHI...")
        self.record_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.view_features_btn.setEnabled(False)

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
            # Lưu file WAV
            audio_data = np.concatenate(self.audio_frames, axis=0)
            audio_data = audio_data * self.gain
            audio_data = np.clip(audio_data, -1.0, 1.0)
            audio_int16 = (audio_data * 32767).astype(np.int16)

            with wave.open(self.current_file, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_int16.tobytes())

            self.status_label.setText(
                f"✅ Đã lưu: {os.path.basename(self.current_file)}")

            # Trích xuất đặc trưng
            self.status_label.setText("📊 Đang trích xuất đặc trưng...")
            QApplication.processEvents()

            try:
                features = extract_features(self.current_file)
                csv_path = self.current_file.replace('.wav', '_features.csv')
                save_features_to_csv(features, csv_path)
                self.last_features_csv = csv_path
                self.view_features_btn.setEnabled(True)
                self.status_label.setText(f"✅ Đã lưu file âm thanh và đặc trưng: {os.path.basename(csv_path)}")
                QMessageBox.information(
                    self, "Thành công", f"Đã lưu:\n- Âm thanh: {self.current_file}\n- Đặc trưng: {csv_path}"
                )
            except Exception as e:
                self.status_label.setText("❌ Lỗi trích xuất đặc trưng")
                QMessageBox.critical(
                    self, "Lỗi", f"Không thể trích xuất đặc trưng:\n{str(e)}")
        else:
            self.status_label.setText("⚠️ Không có dữ liệu")
            QMessageBox.warning(
                self, "Lỗi", "Không ghi được dữ liệu âm thanh.")

        self.record_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.current_file = None

    def show_last_features(self):
        if not self.last_features_csv or not os.path.exists(self.last_features_csv):
            QMessageBox.warning(self, "Lỗi", "Chưa có file đặc trưng nào.")
            return

        import pandas as pd
        df = pd.read_csv(self.last_features_csv)
        features_dict = df.iloc[0].to_dict()

        dialog = QDialog(self)
        dialog.setWindowTitle("Các đặc trưng trích xuất")
        dialog.resize(600, 500)

        layout = QVBoxLayout(dialog)
        table = QTableWidget()
        table.setRowCount(len(features_dict))
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Đặc trưng", "Giá trị"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        for row, (key, value) in enumerate(features_dict.items()):
            table.setItem(row, 0, QTableWidgetItem(key))
            if isinstance(value, float):
                text = f"{value:.6f}"
            else:
                text = str(value)
            table.setItem(row, 1, QTableWidgetItem(text))

        layout.addWidget(table)
        btn_close = QPushButton("Đóng")
        btn_close.clicked.connect(dialog.accept)
        layout.addWidget(btn_close)

        dialog.exec()

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

import sys
import os
import base64

from dotenv import load_dotenv
from openai import OpenAI
from PyQt6.QtWidgets import (
    QApplication, QLabel, QPushButton, QVBoxLayout, QWidget,
    QFileDialog, QTextEdit, QMainWindow, QMessageBox
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

load_dotenv()  # .env 파일에서 OPENAI_API_KEY 등을 읽어옴


class ImageDescriptionApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_pixmap = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('PyQt6 이미지 설명 앱 (OpenAI Vision)')
        self.resize(500, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        self.image_label = QLabel('이미지를 업로드하면 여기에 미리보기가 표시됩니다.')
        self.image_label.setFixedSize(400, 400)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("border: 1px solid gray;")
        layout.addWidget(self.image_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.upload_button = QPushButton('이미지 업로드')
        self.upload_button.clicked.connect(self.upload_image)
        layout.addWidget(self.upload_button)

        self.description_edit = QTextEdit()
        self.description_edit.setReadOnly(True)
        self.description_edit.setPlaceholderText('이미지 설명이 여기에 표시됩니다.')
        layout.addWidget(self.description_edit)

        central_widget.setLayout(layout)

    def upload_image(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, '이미지 파일 선택', '', 'Images (*.png *.jpg *.jpeg *.bmp *.gif)'
        )
        if file_name:
            self.display_image(file_name)
            self.get_image_description(file_name)

    def display_image(self, file_name):
        pixmap = QPixmap(file_name)
        self.current_pixmap = pixmap
        self.update_image_preview()

    def update_image_preview(self):
        if not self.current_pixmap:
            return
        scaled = self.current_pixmap.scaled(
            self.image_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.image_label.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_image_preview()

    def encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def get_image_description(self, file_name):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            QMessageBox.warning(
                self, '설정 오류',
                '.env 파일에 OPENAI_API_KEY가 설정되어 있지 않습니다.'
            )
            self.description_edit.setPlainText('OPENAI_API_KEY가 설정되지 않았습니다.')
            return

        self.description_edit.setPlainText('이미지를 분석하는 중입니다...')
        QApplication.processEvents()

        try:
            base64_image = self.encode_image(file_name)
            ext = os.path.splitext(file_name)[1].lstrip('.').lower() or 'jpeg'
            if ext == 'jpg':
                ext = 'jpeg'

            client = OpenAI(api_key=api_key)
            response = client.responses.create(
                model="gpt-4.1-mini",
                input=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": "이 이미지에 무엇이 있는지 한국어로 자세히 설명해줘."},
                            {
                                "type": "input_image",
                                "image_url": f"data:image/{ext};base64,{base64_image}",
                            },
                        ],
                    }
                ],
                max_output_tokens=500,
            )
            self.description_edit.setPlainText(response.output_text)
        except Exception as e:
            self.description_edit.setPlainText(f"이미지 분석 중 오류가 발생했습니다: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ImageDescriptionApp()
    window.show()
    sys.exit(app.exec())

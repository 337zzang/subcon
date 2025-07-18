import sys
import os

# 프로젝트 루트 경로를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication
from ui.upload_main_window import UploadMainWindow


def main():
    """메인 실행 함수"""
    app = QApplication(sys.argv)
    app.setApplicationName("매입대사 시스템 v2.0")

    # 메인 윈도우 생성 및 표시
    window = UploadMainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

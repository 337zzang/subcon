import sys
from PyQt6.QtWidgets import QApplication
from src.ui.upload_main_window import UploadMainWindow


def main():
    """메인 실행 함수"""
    app = QApplication(sys.argv)
    app.setApplicationName("하도급 대사 시스템")

    # 메인 윈도우 생성 및 표시
    window = UploadMainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

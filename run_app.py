#!/usr/bin/env python
"""
매입대사 시스템 실행 스크립트
"""
import sys
from PyQt6.QtWidgets import QApplication
from src.ui.upload_main_window import UploadMainWindow


def main():
    """메인 실행 함수"""
    app = QApplication(sys.argv)
    app.setApplicationName("매입대사 시스템 v2.0")
    
    # 스타일 설정
    app.setStyle('Fusion')
    
    # 메인 윈도우 생성 및 표시
    window = UploadMainWindow()
    window.setWindowTitle("매입대사 시스템 v2.0")
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

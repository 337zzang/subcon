"""
협력사 매입대사 시스템
Main Entry Point
"""
import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from src.ui.main_window import MainWindow

def main():
    """메인 함수"""
    # 고해상도 디스플레이 지원
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # 애플리케이션 생성
    app = QApplication(sys.argv)
    app.setApplicationName("협력사 매입대사 시스템")
    app.setOrganizationName("SubCon")

    # 스타일 설정 (선택사항)
    app.setStyle("Fusion")

    # 메인 윈도우 생성 및 표시
    window = MainWindow()
    window.show()

    # 애플리케이션 실행
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

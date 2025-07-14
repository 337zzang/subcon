"""
파일 업로드 UI 테스트
"""
import sys
from PyQt6.QtWidgets import QApplication
from src.ui.upload_main_window import UploadMainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 다크 테마 설정 (선택사항)
    # app.setStyleSheet("""
    #     QWidget {
    #         background-color: #2b2b2b;
    #         color: #ffffff;
    #     }
    # """)
    
    window = UploadMainWindow()
    window.show()
    
    sys.exit(app.exec())

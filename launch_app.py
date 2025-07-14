"""
임포트 테스트 및 런처
"""
import sys
import os

# 프로젝트 루트를 sys.path에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print("=== 매입대사 시스템 실행 ===")
print(f"Python Path: {sys.path[0]}")

try:
    # 임포트 테스트
    print("\n1. UI 모듈 임포트 중...")
    from src.ui.main_window_v2 import ImprovedMainWindow
    print("✅ UI 모듈 임포트 성공")
    
    print("\n2. 애플리케이션 시작...")
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    app.setApplicationName("매입대사 시스템 v2.0")
    app.setStyle('Fusion')
    
    # 메인 윈도우 생성 및 표시
    window = ImprovedMainWindow()
    window.setWindowTitle("매입대사 시스템 v2.0")
    window.show()
    
    print("✅ 애플리케이션 시작 완료")
    sys.exit(app.exec())
    
except Exception as e:
    print(f"\n❌ 오류 발생: {type(e).__name__}")
    print(f"상세: {str(e)}")
    import traceback
    traceback.print_exc()
    input("\n엔터를 눌러 종료...")

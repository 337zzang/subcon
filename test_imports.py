"""
임포트 문제 테스트 스크립트
"""
import sys
import os

# 프로젝트 루트와 src를 sys.path에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')

sys.path.insert(0, project_root)
sys.path.insert(0, src_path)

print("=== 임포트 테스트 ===")
print(f"Project Root: {project_root}")
print(f"Src Path: {src_path}")
print(f"sys.path: {sys.path[:3]}")

try:
    print("\n1. models 임포트 테스트...")
    from models import Supplier, Purchase
    print("✅ models 임포트 성공")
except Exception as e:
    print(f"❌ models 임포트 실패: {e}")

try:
    print("\n2. services 임포트 테스트...")
    from services.data_manager import DataManager
    from services.excel_service import ExcelService
    from services.reconciliation_service_v2 import ReconciliationService
    from services.reconciliation_validator import ReconciliationValidator
    print("✅ services 임포트 성공")
except Exception as e:
    print(f"❌ services 임포트 실패: {e}")

try:
    print("\n3. ui 임포트 테스트...")
    from ui.upload_main_window import UploadMainWindow
    from ui.workers.reconciliation_worker import ReconciliationWorker
    print("✅ ui 임포트 성공")
except Exception as e:
    print(f"❌ ui 임포트 실패: {e}")

print("\n✅ 모든 임포트 테스트 완료!")

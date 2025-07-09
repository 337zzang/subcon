"""
대사 프로세스 테스트
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.services.excel_service import ExcelService
from src.services.reconciliation_service import ReconciliationService
import json

def test_reconciliation():
    """대사 프로세스 테스트"""
    # 설정 로드
    with open("config/app_config.json", 'r', encoding='utf-8') as f:
        config = json.load(f)

    # 서비스 초기화
    excel_service = ExcelService()
    reconciliation_service = ReconciliationService(excel_service)

    try:
        print("=== 매입대사 프로세스 테스트 시작 ===")

        # 전체 대사 실행
        results = reconciliation_service.process_all_reconciliation(config)

        print("\n=== 처리 결과 ===")
        for name, df in results.items():
            if hasattr(df, 'shape'):
                print(f"{name}: {df.shape[0]} rows × {df.shape[1]} columns")

        # 결과 저장
        saved_file = reconciliation_service.save_results("OUT")
        print(f"\n✅ 결과 저장: {saved_file}")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_reconciliation()

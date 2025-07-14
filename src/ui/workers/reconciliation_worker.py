"""
백그라운드 대사 처리 Worker
"""
from PyQt6.QtCore import QThread, pyqtSignal
from datetime import datetime
from pathlib import Path
import shutil
import os
import sys

# kfunction 모듈 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from kfunction import read_excel_data

from ...services.reconciliation_service_v2 import ReconciliationService


class ReconciliationWorker(QThread):
    """백그라운드에서 대사 작업을 처리하는 Worker"""
    
    # 시그널 정의
    progress = pyqtSignal(int)        # 진행률 (0-100)
    message = pyqtSignal(str)         # 상태 메시지
    finished = pyqtSignal(dict)       # 완료 시 결과
    error = pyqtSignal(str)           # 오류 발생
    
    def __init__(self, file_paths: dict, start_date: datetime, end_date: datetime):
        super().__init__()
        self.file_paths = file_paths
        self.start_date = start_date
        self.end_date = end_date
        self.is_running = True
        
    def stop(self):
        """작업 중단"""
        self.is_running = False
        
    def run(self):
        """백그라운드 실행"""
        try:
            # 1. 필수 파일 검증
            self.message.emit("📋 필수 파일 검증 중...")
            self.progress.emit(5)
            
            required_files = {
                'purchase_detail': self.file_paths.get('supplier_purchase'),
                'standard': self.file_paths.get('standard'),
                'tax_invoice': self.file_paths.get('tax_invoice'),
                'payment_ledger': self.file_paths.get('payment_ledger'),  # 필수! (키 수정됨)
                'tax_invoice_wis': self.file_paths.get('tax_invoice_wis')
            }
            
            # 필수 파일 체크
            missing_files = []
            for key, path in required_files.items():
                if not path:
                    missing_files.append(key)
                    
            if missing_files:
                self.error.emit(f"필수 파일이 누락되었습니다: {', '.join(missing_files)}")
                return
                
            # 선택 파일
            if 'processing_fee' in self.file_paths:
                required_files['processing_fee'] = self.file_paths['processing_fee']
            
            if not self.is_running:
                return
                
            # 2. 서비스 초기화
            self.message.emit("🔧 대사 서비스 초기화 중...")
            self.progress.emit(10)
            service = ReconciliationService()
            
            # 3. 데이터 로드
            self.message.emit("📥 Excel 파일 로드 중...")
            self.progress.emit(20)
            
            # 파일 경로를 data 폴더로 복사 (임시)
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)
            
            file_map = {}
            for key, src_path in required_files.items():
                if src_path:
                    dest_path = data_dir / Path(src_path).name
                    shutil.copy2(src_path, dest_path)
                    file_map[key] = str(dest_path)
                    
            service.load_all_data(file_map)
            
            if not self.is_running:
                return
                
            # 4. 대사 처리
            self.message.emit("⚙️ 대사 처리 중...")
            self.progress.emit(50)
            
            # 진행률 업데이트를 위한 단계별 처리
            self.message.emit("  - 데이터 전처리 및 피벗...")
            self.progress.emit(60)
            
            self.message.emit("  - 세금계산서 데이터 처리...")
            self.progress.emit(70)
            
            self.message.emit("  - 금액대사 및 순차대사...")
            self.progress.emit(80)
            
            self.message.emit("  - 지불보조장 대사...")
            self.progress.emit(90)
            
            # 실제 대사 처리
            results = service.process_reconciliation(self.start_date, self.end_date)
            
            if not self.is_running:
                return
                
            # 5. 완료
            self.message.emit("✅ 대사 처리 완료!")
            self.progress.emit(100)
            
            # 결과 반환
            self.finished.emit(results)
            
        except Exception as e:
            import traceback
            error_msg = f"대사 처리 중 오류 발생:\n{str(e)}\n\n{traceback.format_exc()}"
            self.error.emit(error_msg)

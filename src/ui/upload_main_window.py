import sys
import os
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QMessageBox, QGroupBox,
    QDateEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QTextEdit, QSplitter, QTabWidget
)
from PyQt6.QtCore import Qt, QDate, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QDragEnterEvent, QDropEvent
import pandas as pd

# 프로젝트 서비스 import
from ..services.data_manager import DataManager
from ..services.excel_service import ExcelService
from ..services.reconciliation_service import ReconciliationService


class ReconciliationThread(QThread):
    """대사 처리를 위한 별도 스레드"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, data_manager, start_date, end_date):
        super().__init__()
        self.data_manager = data_manager
        self.start_date = start_date
        self.end_date = end_date
        self.results = None

    def run(self):
        try:
            self.progress.emit(10, "대사 처리 시작...")

            # ReconciliationService 생성
            service = ReconciliationService(self.data_manager)

            self.progress.emit(50, "데이터 매칭 중...")

            # 대사 처리 실행
            self.results = service.process_all_reconciliation(
                self.start_date, self.end_date
            )

            self.progress.emit(100, "대사 처리 완료!")
            self.finished.emit(self.results)

        except Exception as e:
            self.error.emit(str(e))


class FileUploadWidget(QWidget):
    """파일 업로드를 위한 커스텀 위젯"""
    fileUploaded = pyqtSignal(str, str)  # 파일 경로, 파일 타입

    def __init__(self, file_type: str, file_description: str):
        super().__init__()
        self.file_type = file_type
        self.file_description = file_description
        self.file_path = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # 파일 타입 라벨
        type_label = QLabel(f"📄 {self.file_description}")
        type_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        layout.addWidget(type_label)

        # 드래그 앤 드롭 영역
        self.drop_area = QLabel("파일을 여기에 드래그하거나\n클릭하여 선택하세요")
        self.drop_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_area.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 10px;
                padding: 30px;
                background-color: #f5f5f5;
                min-height: 100px;
            }
            QLabel:hover {
                background-color: #e8e8e8;
                border-color: #666;
            }
        """)
        self.drop_area.setCursor(Qt.CursorShape.PointingHandCursor)
        self.drop_area.mousePressEvent = self.select_file
        layout.addWidget(self.drop_area)

        # 파일 정보 라벨
        self.file_info = QLabel("파일 없음")
        self.file_info.setStyleSheet("color: #666; font-size: 10pt;")
        layout.addWidget(self.file_info)

        # 검증 상태 라벨
        self.validation_status = QLabel("")
        layout.addWidget(self.validation_status)

        self.setLayout(layout)
        self.setAcceptDrops(True)

    def select_file(self, event=None):
        """파일 선택 다이얼로그"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"{self.file_description} 선택",
            "",
            "Excel Files (*.xlsx *.xls);;All Files (*.*)"
        )

        if file_path:
            self.process_file(file_path)

    def process_file(self, file_path: str):
        """파일 처리 및 검증"""
        self.file_path = file_path
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path) / 1024 / 1024  # MB

        # 파일 정보 업데이트
        self.file_info.setText(f"파일: {file_name} ({file_size:.2f} MB)")
        self.drop_area.setText(f"✅ {file_name}")

        # 파일 검증
        if self.validate_file(file_path):
            self.validation_status.setText("✅ 파일 검증 완료")
            self.validation_status.setStyleSheet("color: green;")
            self.fileUploaded.emit(file_path, self.file_type)
        else:
            self.validation_status.setText("❌ 파일 검증 실패")
            self.validation_status.setStyleSheet("color: red;")

    def validate_file(self, file_path: str) -> bool:
        """파일 검증 로직"""
        try:
            # Excel 파일 읽기 시도
            df = pd.read_excel(file_path, nrows=5)

            # 파일 타입별 검증 (매입대사2.ipynb 참고)
            if self.file_type == "supplier":
                # 공급업체 파일 검증
                required_cols = ["사업자등록번호", "상호명"]
                if not all(col in df.columns for col in required_cols):
                    self.validation_status.setText(f"❌ 필수 컬럼 누락: {required_cols}")
                    return False
            elif self.file_type == "purchase":
                # 구매 파일 검증 (df_book과 유사)
                return True
            elif self.file_type == "payment":
                # 지급 파일 검증
                return True
            elif self.file_type == "tax_invoice":
                # 세금계산서 파일 검증 (df_tax_hifi와 유사)
                return True

            return True

        except Exception as e:
            self.validation_status.setText(f"❌ 파일 읽기 오류: {str(e)}")
            return False

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files and files[0].endswith(('.xlsx', '.xls')):
            self.process_file(files[0])


class UploadMainWindow(QMainWindow):
    """파일 업로드 기반 메인 윈도우"""

    def __init__(self):
        super().__init__()
        self.uploaded_files = {}
        self.data_manager = DataManager()
        self.reconciliation_results = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("하도급 대사 시스템 - 파일 업로드")
        self.setGeometry(100, 100, 1200, 800)

        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 메인 레이아웃
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # 상단: 기간 선택
        date_group = QGroupBox("대사 기간 선택")
        date_layout = QHBoxLayout()

        date_layout.addWidget(QLabel("시작일:"))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate(2024, 1, 1))  # 2024-01-01
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        date_layout.addWidget(self.start_date)

        date_layout.addWidget(QLabel("종료일:"))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate(2024, 6, 30))  # 2024-06-30
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        date_layout.addWidget(self.end_date)

        date_layout.addStretch()
        date_group.setLayout(date_layout)
        main_layout.addWidget(date_group)

        # 중앙: 파일 업로드 영역
        upload_group = QGroupBox("파일 업로드")
        upload_layout = QHBoxLayout()

        # 파일 업로드 위젯들
        self.file_widgets = {
            'supplier': FileUploadWidget('supplier', '공급업체 마스터'),
            'purchase': FileUploadWidget('purchase', '구매 내역'),
            'payment': FileUploadWidget('payment', '지급 내역'),
            'tax_invoice': FileUploadWidget('tax_invoice', '세금계산서'),
        }

        for widget in self.file_widgets.values():
            widget.fileUploaded.connect(self.on_file_uploaded)
            upload_layout.addWidget(widget)

        upload_group.setLayout(upload_layout)
        main_layout.addWidget(upload_group)

        # 하단: 실행 버튼 및 상태
        control_layout = QHBoxLayout()

        # 대사 실행 버튼
        self.process_btn = QPushButton("📊 대사 실행")
        self.process_btn.setEnabled(False)
        self.process_btn.clicked.connect(self.process_reconciliation)
        self.process_btn.setStyleSheet("""
            QPushButton {
                font-size: 14pt;
                padding: 10px 30px;
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        control_layout.addWidget(self.process_btn)

        # 결과 다운로드 버튼
        self.download_btn = QPushButton("💾 결과 다운로드")
        self.download_btn.setEnabled(False)
        self.download_btn.clicked.connect(self.download_results)
        self.download_btn.setStyleSheet("""
            QPushButton {
                font-size: 14pt;
                padding: 10px 30px;
                background-color: #2196F3;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        control_layout.addWidget(self.download_btn)

        control_layout.addStretch()
        main_layout.addLayout(control_layout)

        # 진행 상태 바
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # 로그 영역
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        main_layout.addWidget(self.log_text)

        self.add_log("시스템 준비 완료. 파일을 업로드해주세요.")

    def on_file_uploaded(self, file_path: str, file_type: str):
        """파일 업로드 완료 처리"""
        self.uploaded_files[file_type] = file_path
        self.add_log(f"{file_type} 파일 업로드 완료: {os.path.basename(file_path)}")

        # 데이터 로드 시도
        try:
            self.load_data_from_file(file_path, file_type)
        except Exception as e:
            self.add_log(f"❌ {file_type} 데이터 로드 실패: {str(e)}")
            return

        # 모든 필수 파일이 업로드되었는지 확인
        required_files = ['supplier', 'purchase', 'payment', 'tax_invoice']
        if all(f in self.uploaded_files for f in required_files):
            self.process_btn.setEnabled(True)
            self.add_log("✅ 모든 파일이 준비되었습니다. 대사를 실행할 수 있습니다.")

    def load_data_from_file(self, file_path: str, file_type: str):
        """파일에서 데이터 로드"""
        try:
            if file_type == 'supplier':
                # 공급업체 데이터 로드
                suppliers = ExcelService.load_suppliers(file_path)
                for supplier in suppliers:
                    self.data_manager.add_supplier(supplier)
                self.add_log(f"  - {len(suppliers)}개 공급업체 로드 완료")

            elif file_type == 'purchase':
                # 구매 데이터 로드
                purchases = ExcelService.load_purchases(file_path)
                for purchase in purchases:
                    self.data_manager.add_purchase(purchase)
                self.add_log(f"  - {len(purchases)}개 구매 내역 로드 완료")

            elif file_type == 'payment':
                # 지급 데이터 로드
                payments = ExcelService.load_payments(file_path)
                self.data_manager.payments.extend(payments)
                self.add_log(f"  - {len(payments)}개 지급 내역 로드 완료")

            elif file_type == 'tax_invoice':
                # 세금계산서 데이터 로드
                tax_invoices = ExcelService.load_tax_invoices(file_path)
                self.data_manager.tax_invoices.extend(tax_invoices)
                self.add_log(f"  - {len(tax_invoices)}개 세금계산서 로드 완료")

        except Exception as e:
            raise Exception(f"{file_type} 데이터 로드 실패: {str(e)}")

    def process_reconciliation(self):
        """대사 처리 실행"""
        self.add_log("대사 처리를 시작합니다...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.process_btn.setEnabled(False)

        # 날짜 가져오기
        start_date = self.start_date.date().toPyDate()
        end_date = self.end_date.date().toPyDate()

        # 별도 스레드에서 대사 처리 실행
        self.worker = ReconciliationThread(self.data_manager, start_date, end_date)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_reconciliation_finished)
        self.worker.error.connect(self.on_reconciliation_error)
        self.worker.start()

    def update_progress(self, value: int, message: str):
        """진행 상태 업데이트"""
        self.progress_bar.setValue(value)
        self.add_log(message)

    def on_reconciliation_finished(self, results: dict):
        """대사 처리 완료"""
        self.reconciliation_results = results
        self.add_log("✅ 대사 처리가 완료되었습니다!")
        self.add_log(f"  - 전체: {results['summary']['total_count']}건")
        self.add_log(f"  - 완전 매칭: {results['summary']['complete_count']}건")
        self.add_log(f"  - 부분 매칭: {results['summary']['partial_count']}건")
        self.add_log(f"  - 미매칭: {results['summary']['unmatched_count']}건")
        self.download_btn.setEnabled(True)
        self.process_btn.setEnabled(True)

    def on_reconciliation_error(self, error_msg: str):
        """대사 처리 오류"""
        self.add_log(f"❌ 대사 처리 중 오류 발생: {error_msg}")
        self.progress_bar.setVisible(False)
        self.process_btn.setEnabled(True)

    def download_results(self):
        """결과 다운로드"""
        if not self.reconciliation_results:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "결과 파일 저장",
            f"대사결과_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            "Excel Files (*.xlsx)"
        )

        if file_path:
            try:
                # ReconciliationService의 export 메서드 사용
                service = ReconciliationService(self.data_manager)
                service.export_results_to_excel(self.reconciliation_results, file_path)
                self.add_log(f"✅ 결과가 저장되었습니다: {file_path}")

                # 파일 열기 제안
                reply = QMessageBox.question(
                    self, "파일 열기", 
                    "저장된 파일을 열어보시겠습니까?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    os.startfile(file_path)

            except Exception as e:
                self.add_log(f"❌ 파일 저장 중 오류: {str(e)}")

    def add_log(self, message: str):
        """로그 메시지 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = UploadMainWindow()
    window.show()
    sys.exit(app.exec())

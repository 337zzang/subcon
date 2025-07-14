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
from PyQt6.QtCore import Qt, QDate, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QPixmap, QDragEnterEvent, QDropEvent
import pandas as pd

# kfunction 모듈 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from kfunction import read_excel_data

# 프로젝트 서비스 import - 절대 임포트로 변경
from src.services.data_manager import DataManager
from src.services.excel_service import ExcelService
from src.services.reconciliation_service_v2 import ReconciliationService


class FileUploadThread(QThread):
    """파일 업로드를 위한 별도 스레드"""
    progress = pyqtSignal(int, str)  # 진행률, 메시지
    finished = pyqtSignal(bool, str)  # 성공 여부, 메시지
    validation_result = pyqtSignal(bool, str)  # 검증 결과, 메시지
    data_loaded = pyqtSignal(str, object)  # 파일 타입, 데이터
    
    def __init__(self, file_path, file_type):
        super().__init__()
        self.file_path = file_path
        self.file_type = file_type
        
    def run(self):
        try:
            self.progress.emit(20, "파일 검증 중...")
            
            # 파일 검증 및 데이터 로드
            is_valid, message, data = self.validate_and_load_file()
            self.validation_result.emit(is_valid, message)
            
            if not is_valid:
                self.finished.emit(False, message)
                return
                
            self.progress.emit(50, "파일 읽기 완료...")
            
            # 데이터를 메인 스레드로 전달
            if data is not None:
                self.data_loaded.emit(self.file_type, data)
            
            self.progress.emit(100, "업로드 완료!")
            self.finished.emit(True, "파일 업로드가 완료되었습니다.")
            
        except Exception as e:
            self.finished.emit(False, f"업로드 실패: {str(e)}")
            
    def validate_and_load_file(self):
        """파일 검증 및 데이터 로드 (한 번만 읽기)"""
        try:
            # 파일 크기 확인
            file_size = os.path.getsize(self.file_path) / 1024 / 1024  # MB
            if file_size > 10:
                print(f"큰 파일 처리 중: {file_size:.1f}MB")
            
            # Excel 파일 읽기 (한 번만!)
            print(f"[INFO] '{self.file_path}' 읽는 중…")
            df = read_excel_data(self.file_path)
            
            if df.empty:
                return False, "빈 파일입니다.", None

            # 파일 타입별 검증
            if self.file_type == "supplier_purchase":
                # 협력사단품별매입 파일 검증
                required_cols = ['협력사코드', '협력사명']
                if not all(col in df.columns for col in required_cols):
                    return False, f"필수 컬럼이 없습니다: {required_cols}", None
                return True, "검증 완료", df
                
            elif self.file_type == "standard":
                # 기준 파일 검증
                return True, "검증 완료", df
                
            elif self.file_type == "tax_invoice":
                # 매입세금계산서 파일 검증
                return True, "검증 완료", df
                
            elif self.file_type == "payment_ledger":
                # 지불보조장 파일 검증
                return True, "검증 완료", df
                
            elif self.file_type == "tax_invoice_wis":
                # 매입세금계산서(WIS) 파일 검증
                return True, "검증 완료", df

            return True, "검증 완료", df

        except Exception as e:
            return False, f"파일 읽기 오류: {str(e)}", None


class DataLoadThread(QThread):
    """데이터 로드를 위한 별도 스레드"""
    progress = pyqtSignal(str)  # 메시지
    finished = pyqtSignal(bool, str)  # 성공 여부, 메시지
    
    def __init__(self, data_manager, file_path, file_type, cached_data=None):
        super().__init__()
        self.data_manager = data_manager
        self.file_path = file_path
        self.file_type = file_type
        self.cached_data = cached_data  # 캐싱된 데이터
        
    def run(self):
        try:
            # 캐싱된 데이터가 있으면 사용, 없으면 다시 읽기
            if self.cached_data is not None:
                df = self.cached_data
                self.progress.emit("캐싱된 데이터 사용")
            else:
                # 캐시에서 확인
                df = self.data_manager.get_cached_data(self.file_path)
                if df is None:
                    # 캐시에 없으면 파일 읽기
                    print(f"[INFO] 캐시 미스 - '{self.file_path}' 다시 읽는 중…")
                    df = read_excel_data(self.file_path)
                    self.data_manager.cache_file_data(self.file_path, df)
                else:
                    self.progress.emit("캐시에서 데이터 로드")
            
            # 파일 타입별 데이터 처리
            if self.file_type == 'supplier_purchase':
                # 협력사단품별매입 데이터 로드
                self.data_manager.load_purchases_from_df(df)
                self.data_manager.load_suppliers_from_df(df)
                self.progress.emit(f"협력사단품별매입 데이터 로드 완료 - {len(df)}행")
                
            elif self.file_type == 'standard':
                # 기준 데이터 로드
                self.progress.emit(f"기준 데이터 로드 완료 - {len(df)}행")
                
            elif self.file_type == 'tax_invoice':
                # 세금계산서 데이터 로드
                tax_invoices = ExcelService.load_tax_invoices(self.file_path, df)
                self.data_manager.tax_invoices.extend(tax_invoices)
                self.progress.emit(f"{len(tax_invoices)}개 세금계산서 로드 완료")
                
            elif self.file_type == 'payment_ledger':
                # 지불보조장 데이터 로드
                self.progress.emit(f"지불보조장 데이터 로드 완료 - {len(df)}행")
                
            elif self.file_type == 'tax_invoice_wis':
                # 세금계산서(WIS) 데이터 로드
                self.progress.emit(f"세금계산서(WIS) 데이터 로드 완료 - {len(df)}행")
                
            self.finished.emit(True, "데이터 로드 완료")
            
        except Exception as e:
            self.finished.emit(False, f"데이터 로드 실패: {str(e)}")


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
    fileUploaded = pyqtSignal(str, str, object)  # 파일 경로, 파일 타입, 데이터

    def __init__(self, file_type: str, file_description: str):
        super().__init__()
        self.file_type = file_type
        self.file_description = file_description
        self.file_path = None
        self.upload_thread = None
        self.is_uploading = False
        self.loaded_data = None  # 로드된 데이터 저장
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

        # 상태 라벨
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.status_label)
        
        # 진행률 바
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # 검증 상태 라벨
        self.validation_status = QLabel("")
        layout.addWidget(self.validation_status)

        self.setLayout(layout)
        self.setAcceptDrops(True)

    def select_file(self, event=None):
        """파일 선택 다이얼로그"""
        # 업로드 중이면 새 파일 선택 허용하지 않음
        # 사용자 요청에 따라 업로드 중에도 다른 파일 선택 가능하도록 수정
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
        # 이미 업로드 중인 경우 스레드 정리
        if self.upload_thread and self.upload_thread.isRunning():
            self.upload_thread.terminate()
            self.upload_thread.wait()
            
        self.file_path = file_path
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path) / 1024 / 1024  # MB

        # 파일 정보 업데이트
        self.file_info.setText(f"파일: {file_name} ({file_size:.2f} MB)")
        self.drop_area.setText(f"📁 {file_name}")
        
        # 상태를 "업로드중"으로 변경
        self.status_label.setText("🔄 업로드중...")
        self.status_label.setStyleSheet("color: #FF8C00; font-weight: bold;")
        self.validation_status.setText("")
        
        # 진행률 바 표시
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 백그라운드 스레드에서 업로드 처리
        self.upload_thread = FileUploadThread(file_path, self.file_type)
        self.upload_thread.progress.connect(self.update_progress)
        self.upload_thread.validation_result.connect(self.on_validation_result)
        self.upload_thread.data_loaded.connect(self.on_data_loaded)  # 데이터 로드 시그널 연결
        self.upload_thread.finished.connect(self.on_upload_finished)
        self.upload_thread.start()
        
        self.is_uploading = True

    def update_progress(self, value: int, message: str):
        """진행률 업데이트"""
        self.progress_bar.setValue(value)
        self.status_label.setText(f"🔄 {message}")

    def on_data_loaded(self, file_type: str, data):
        """데이터 로드 완료 처리"""
        self.loaded_data = data
        
    def on_validation_result(self, is_valid: bool, message: str):
        """검증 결과 처리"""
        if is_valid:
            self.validation_status.setText(f"✅ {message}")
            self.validation_status.setStyleSheet("color: green;")
        else:
            self.validation_status.setText(f"❌ {message}")
            self.validation_status.setStyleSheet("color: red;")

    def on_upload_finished(self, success: bool, message: str):
        """업로드 완료 처리"""
        self.is_uploading = False
        self.progress_bar.setVisible(False)
        
        if success:
            self.status_label.setText("✅ 확인")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.drop_area.setText(f"✅ {os.path.basename(self.file_path)}")
            # 데이터와 함께 시그널 발생
            self.fileUploaded.emit(self.file_path, self.file_type, self.loaded_data)
        else:
            self.status_label.setText("❌ 실패")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.validation_status.setText(message)
            self.validation_status.setStyleSheet("color: red;")

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
        self.data_load_threads = {}  # 각 파일 타입별 데이터 로드 스레드
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("하도급 매입대사 시스템 v2.0")
        self.setGeometry(100, 100, 1400, 900)
        
        # 전체 스타일 설정
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)

        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 메인 레이아웃
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        central_widget.setLayout(main_layout)

        # 상단 타이틀
        title = QLabel("📋 하도급 매입대사 시스템")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 20pt;
            font-weight: bold;
            padding: 10px;
            background-color: #2196F3;
            color: white;
            border-radius: 5px;
        """)
        main_layout.addWidget(title)

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
        upload_layout = QVBoxLayout()
        
        # 파일 업로드 위젯 컨테이너
        file_container = QHBoxLayout()

        # 파일 업로드 위젯들
        self.file_widgets = {
            'supplier_purchase': FileUploadWidget('supplier_purchase', '협력사단품별매입'),
            'standard': FileUploadWidget('standard', '기준 파일'),
            'tax_invoice': FileUploadWidget('tax_invoice', '매입세금계산서'),
            'payment_ledger': FileUploadWidget('payment_ledger', '지불보조장'),
            'tax_invoice_wis': FileUploadWidget('tax_invoice_wis', '매입세금계산서(WIS)')
        }

        for widget in self.file_widgets.values():
            widget.fileUploaded.connect(self.on_file_uploaded)
            file_container.addWidget(widget)

        upload_layout.addLayout(file_container)
        
        # 파일 상태 요약
        self.status_summary = QLabel("파일 업로드 대기중...")
        self.status_summary.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #f0f0f0;
                border-radius: 5px;
                font-size: 11pt;
            }
        """)
        upload_layout.addWidget(self.status_summary)
        
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
        log_group = QGroupBox("실행 로그")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-family: Consolas, monospace;
                font-size: 10pt;
            }
        """)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)

        self.add_log("🚀 시스템 준비 완료. 파일을 업로드해주세요.")

    def on_file_uploaded(self, file_path: str, file_type: str, data=None):
        """파일 업로드 완료 처리"""
        self.uploaded_files[file_type] = file_path
        self.add_log(f"📁 {file_type} 파일 업로드 완료: {os.path.basename(file_path)}")
        
        # 데이터가 있으면 캐싱
        if data is not None:
            self.data_manager.cache_file_data(file_path, data)
            self.add_log(f"  - 데이터 캐싱 완료 ({len(data)}행)")

        # 백그라운드에서 데이터 로드
        if file_type in self.data_load_threads and self.data_load_threads[file_type].isRunning():
            self.data_load_threads[file_type].terminate()
            self.data_load_threads[file_type].wait()
            
        self.add_log(f"🔄 {file_type} 데이터 로드 중...")
        
        # 캐싱된 데이터와 함께 DataLoadThread 생성
        load_thread = DataLoadThread(self.data_manager, file_path, file_type, data)
        load_thread.progress.connect(lambda msg: self.add_log(f"  - {msg}"))
        load_thread.finished.connect(lambda success, msg: self.on_data_loaded(file_type, success, msg))
        load_thread.start()
        
        self.data_load_threads[file_type] = load_thread

    def on_data_loaded(self, file_type: str, success: bool, message: str):
        """데이터 로드 완료 처리"""
        if success:
            self.add_log(f"✅ {file_type} {message}")
        else:
            self.add_log(f"❌ {file_type} {message}")
            # 실패한 경우 업로드 목록에서 제거
            if file_type in self.uploaded_files:
                del self.uploaded_files[file_type]
            return

        # 모든 필수 파일이 업로드되었는지 확인
        required_files = ['supplier_purchase', 'standard', 'tax_invoice', 'payment_ledger', 'tax_invoice_wis']
        if all(f in self.uploaded_files for f in required_files):
            # 모든 데이터 로드 스레드가 완료되었는지 확인
            all_loaded = True
            for f in required_files:
                if f in self.data_load_threads and self.data_load_threads[f].isRunning():
                    all_loaded = False
                    break
                    
            if all_loaded:
                self.process_btn.setEnabled(True)
                self.add_log("✅ 모든 파일이 준비되었습니다. 대사를 실행할 수 있습니다.")
                
                # 파일 상태 요약 표시
                self.add_log("\n📊 파일 업로드 상태:")
                for file_type, widget in self.file_widgets.items():
                    if file_type in self.uploaded_files:
                        self.add_log(f"  ✅ {widget.file_description}")
                    else:
                        self.add_log(f"  ⭕ {widget.file_description} - 대기중")
                        
                self.update_status_summary()
        else:
            self.update_status_summary()
            
    def update_status_summary(self):
        """파일 상태 요약 업데이트"""
        uploaded_count = len(self.uploaded_files)
        total_count = 5  # 5개 필수 파일
        
        if uploaded_count == 0:
            self.status_summary.setText("파일 업로드 대기중...")
            self.status_summary.setStyleSheet("""
                QLabel {
                    padding: 10px;
                    background-color: #f0f0f0;
                    border-radius: 5px;
                    font-size: 11pt;
                }
            """)
        elif uploaded_count < total_count:
            status_text = f"업로드 진행중: {uploaded_count}/{total_count} ("
            status_parts = []
            for file_type, widget in self.file_widgets.items():
                if file_type in self.uploaded_files:
                    status_parts.append(f"✅ {widget.file_description}")
                else:
                    status_parts.append(f"⭕ {widget.file_description}")
            status_text += ", ".join(status_parts) + ")"
            
            self.status_summary.setText(status_text)
            self.status_summary.setStyleSheet("""
                QLabel {
                    padding: 10px;
                    background-color: #FFF3CD;
                    border: 1px solid #FFEAA7;
                    border-radius: 5px;
                    font-size: 11pt;
                    color: #856404;
                }
            """)
        else:
            self.status_summary.setText("✅ 모든 파일 업로드 완료! 대사 실행 준비 완료")
            self.status_summary.setStyleSheet("""
                QLabel {
                    padding: 10px;
                    background-color: #D4EDDA;
                    border: 1px solid #C3E6CB;
                    border-radius: 5px;
                    font-size: 11pt;
                    color: #155724;
                }
            """)

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
        
        # 색상 코드 처리
        color_map = {
            "✅": "green",
            "❌": "red",
            "🔄": "#FF8C00",  # 오렌지
            "📁": "blue",
            "📊": "#4CAF50",
            "⭕": "#999999"
        }
        
        color = "black"
        for emoji, emoji_color in color_map.items():
            if message.startswith(emoji):
                color = emoji_color
                break
                
        self.log_text.append(f'<span style="color: gray">[{timestamp}]</span> <span style="color: {color}">{message}</span>')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = UploadMainWindow()
    window.show()
    sys.exit(app.exec())

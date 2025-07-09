"""
개선된 메인 윈도우 UI - 파일 업로드 방식
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QGroupBox,
    QFileDialog, QMessageBox, QProgressBar, QTableWidget,
    QTableWidgetItem, QTextEdit, QSplitter, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor
import pandas as pd
from typing import Dict, Optional
from pathlib import Path
from datetime import datetime
import json

from src.services.excel_service import ExcelService
from src.services.reconciliation_service import ReconciliationService

class FileUploadWidget(QWidget):
    """파일 업로드 위젯"""
    file_uploaded = pyqtSignal(str, str)  # (file_type, file_path)

    def __init__(self, file_type: str, file_label: str):
        super().__init__()
        self.file_type = file_type
        self.file_path = None
        self.init_ui(file_label)

    def init_ui(self, file_label: str):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # 파일 라벨
        self.label = QLabel(file_label)
        self.label.setMinimumWidth(200)

        # 파일 경로 표시
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        self.path_edit.setPlaceholderText("파일을 선택하세요...")

        # 업로드 버튼
        self.btn_upload = QPushButton("📂 파일 선택")
        self.btn_upload.clicked.connect(self.select_file)

        # 상태 표시
        self.status_label = QLabel("⏳ 대기")
        self.status_label.setMinimumWidth(60)

        layout.addWidget(self.label)
        layout.addWidget(self.path_edit)
        layout.addWidget(self.btn_upload)
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def select_file(self):
        """파일 선택"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"{self.label.text()} 선택",
            "",
            "Excel Files (*.xlsx *.xls);;All Files (*.*)"
        )

        if file_path:
            self.file_path = file_path
            self.path_edit.setText(Path(file_path).name)
            self.validate_file()

    def validate_file(self):
        """파일 검증"""
        try:
            # 간단한 검증 - 파일을 열 수 있는지 확인
            pd.read_excel(self.file_path, nrows=1)
            self.status_label.setText("✅ 확인")
            self.status_label.setStyleSheet("color: green;")
            self.file_uploaded.emit(self.file_type, self.file_path)
        except Exception as e:
            self.status_label.setText("❌ 오류")
            self.status_label.setStyleSheet("color: red;")
            QMessageBox.warning(self, "파일 오류", f"파일을 읽을 수 없습니다:\n{str(e)}")

    def reset(self):
        """초기화"""
        self.file_path = None
        self.path_edit.clear()
        self.status_label.setText("⏳ 대기")
        self.status_label.setStyleSheet("")

class ReconciliationThread(QThread):
    """대사 처리 스레드"""
    progress = pyqtSignal(int)
    message = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, file_paths: Dict[str, str], selected_months: list):
        super().__init__()
        self.file_paths = file_paths
        self.selected_months = selected_months

    def run(self):
        try:
            self.message.emit("대사 프로세스 시작...")
            self.progress.emit(10)

            # 임시 설정 생성
            config = {
                'excel_files': {
                    'supplier_purchase': Path(self.file_paths['supplier_purchase']).name,
                    'standard': Path(self.file_paths['standard']).name,
                    'tax_invoice': Path(self.file_paths['tax_invoice']).name,
                    'tax_invoice_wis': Path(self.file_paths['tax_invoice_wis']).name,
                    'payment_ledger': Path(self.file_paths.get('payment_ledger', '')).name,
                    'processing_fee': Path(self.file_paths.get('processing_fee', '')).name
                }
            }

            # 서비스 초기화
            excel_service = ExcelService()
            reconciliation_service = ReconciliationService(excel_service)

            # 파일 경로를 직접 사용하도록 수정 필요
            # 여기서는 임시로 data 폴더에 복사하는 방식 사용
            import shutil
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)

            for file_type, file_path in self.file_paths.items():
                if file_path:
                    dest = data_dir / Path(file_path).name
                    shutil.copy2(file_path, dest)

            self.progress.emit(30)

            # 대사 실행
            results = reconciliation_service.process_all_reconciliation(config)

            # 선택한 월로 필터링
            if self.selected_months and 'reconciliation_result' in results:
                df = results['reconciliation_result']
                df['년월_str'] = df['년월'].astype(str)
                df_filtered = df[df['년월_str'].isin(self.selected_months)]
                results['reconciliation_result'] = df_filtered

            self.progress.emit(100)
            self.message.emit("대사 완료!")
            self.finished.emit(results)

        except Exception as e:
            self.error.emit(str(e))

class ImprovedMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.file_paths = {}
        self.current_results = None
        self.init_ui()

    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("협력사 매입대사 시스템 v2.0")
        self.setGeometry(100, 100, 1400, 800)

        # 스타일 설정
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)

        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 메인 레이아웃
        main_layout = QVBoxLayout(central_widget)

        # 제목
        title_label = QLabel("📊 협력사 매입대사 시스템")
        title_font = QFont("맑은 고딕", 18, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # 스플리터
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 왼쪽 패널 (파일 업로드)
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)

        # 오른쪽 패널 (결과/로그)
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)

        splitter.setSizes([700, 700])
        main_layout.addWidget(splitter)

        # 하단 상태바
        self.status_bar = self.statusBar()
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)

    def create_left_panel(self) -> QWidget:
        """왼쪽 패널 생성 (파일 업로드)"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # 1. 파일 업로드 섹션
        file_group = QGroupBox("📁 파일 업로드")
        file_layout = QVBoxLayout()

        # 필수 파일들
        self.file_widgets = {}

        required_files = [
            ('supplier_purchase', '협력사단품별매입 (필수)', True),
            ('standard', '기준 파일 (필수)', True),
            ('tax_invoice', '매입세금계산서 (필수)', True),
            ('tax_invoice_wis', '매입세금계산서(WIS) (필수)', True),
            ('payment_ledger', '지불보조장 (선택)', False),
            ('processing_fee', '임가공비 (선택)', False)
        ]

        for file_type, label, required in required_files:
            if required:
                label = f"* {label}"
            widget = FileUploadWidget(file_type, label)
            widget.file_uploaded.connect(self.on_file_uploaded)
            self.file_widgets[file_type] = widget
            file_layout.addWidget(widget)

        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # 2. 기간 선택 섹션
        period_group = QGroupBox("📅 대사 기간 선택")
        period_layout = QVBoxLayout()

        # 년도 선택
        year_layout = QHBoxLayout()
        year_layout.addWidget(QLabel("년도:"))
        self.year_combo = QComboBox()
        current_year = datetime.now().year
        for year in range(current_year - 2, current_year + 1):
            self.year_combo.addItem(str(year))
        self.year_combo.setCurrentText(str(current_year))
        year_layout.addWidget(self.year_combo)
        year_layout.addStretch()
        period_layout.addLayout(year_layout)

        # 월 선택 (체크박스)
        month_label = QLabel("월 선택 (복수 선택 가능):")
        period_layout.addWidget(month_label)

        month_grid = QGridLayout()
        self.month_checkboxes = {}

        from PyQt6.QtWidgets import QCheckBox
        for i in range(12):
            month = i + 1
            checkbox = QCheckBox(f"{month}월")
            checkbox.setChecked(True)  # 기본적으로 모두 선택
            self.month_checkboxes[month] = checkbox
            month_grid.addWidget(checkbox, i // 6, i % 6)

        # 전체 선택/해제 버튼
        btn_layout = QHBoxLayout()
        btn_all = QPushButton("전체 선택")
        btn_all.clicked.connect(lambda: self.toggle_months(True))
        btn_none = QPushButton("전체 해제")
        btn_none.clicked.connect(lambda: self.toggle_months(False))
        btn_layout.addWidget(btn_all)
        btn_layout.addWidget(btn_none)
        btn_layout.addStretch()

        period_layout.addLayout(month_grid)
        period_layout.addLayout(btn_layout)
        period_group.setLayout(period_layout)
        layout.addWidget(period_group)

        # 3. 실행 버튼
        execute_group = QGroupBox("⚡ 실행")
        execute_layout = QVBoxLayout()

        self.btn_validate = QPushButton("🔍 파일 검증")
        self.btn_validate.clicked.connect(self.validate_all_files)

        self.btn_execute = QPushButton("🚀 대사 실행")
        self.btn_execute.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 16px;
                padding: 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.btn_execute.clicked.connect(self.execute_reconciliation)
        self.btn_execute.setEnabled(False)

        execute_layout.addWidget(self.btn_validate)
        execute_layout.addWidget(self.btn_execute)
        execute_group.setLayout(execute_layout)
        layout.addWidget(execute_group)

        layout.addStretch()
        return panel

    def create_right_panel(self) -> QWidget:
        """오른쪽 패널 생성 (결과/로그)"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # 결과 섹션
        result_group = QGroupBox("📊 대사 결과")
        result_layout = QVBoxLayout()

        # 요약 정보
        self.summary_label = QLabel("대사를 실행하면 결과가 여기에 표시됩니다.")
        result_layout.addWidget(self.summary_label)

        # 결과 테이블
        self.result_table = QTableWidget()
        self.result_table.setAlternatingRowColors(True)
        result_layout.addWidget(self.result_table)

        # 다운로드 버튼
        btn_layout = QHBoxLayout()
        self.btn_download = QPushButton("💾 결과 다운로드 (Excel)")
        self.btn_download.clicked.connect(self.download_results)
        self.btn_download.setEnabled(False)
        btn_layout.addWidget(self.btn_download)
        btn_layout.addStretch()
        result_layout.addLayout(btn_layout)

        result_group.setLayout(result_layout)
        layout.addWidget(result_group, 3)

        # 로그 섹션
        log_group = QGroupBox("📜 처리 로그")
        log_layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        log_layout.addWidget(self.log_text)

        log_group.setLayout(log_layout)
        layout.addWidget(log_group, 1)

        return panel

    def on_file_uploaded(self, file_type: str, file_path: str):
        """파일 업로드 처리"""
        self.file_paths[file_type] = file_path
        self.log(f"✅ {file_type} 파일 업로드: {Path(file_path).name}")

        # 필수 파일이 모두 업로드되었는지 확인
        required_files = ['supplier_purchase', 'standard', 'tax_invoice', 'tax_invoice_wis']
        all_uploaded = all(f in self.file_paths for f in required_files)

        if all_uploaded:
            self.btn_execute.setEnabled(True)
            self.log("✅ 모든 필수 파일이 업로드되었습니다. 대사를 실행할 수 있습니다.")

    def toggle_months(self, checked: bool):
        """월 전체 선택/해제"""
        for checkbox in self.month_checkboxes.values():
            checkbox.setChecked(checked)

    def validate_all_files(self):
        """모든 파일 검증"""
        self.log("=== 파일 검증 시작 ===")

        for file_type, widget in self.file_widgets.items():
            if widget.file_path:
                widget.validate_file()
            else:
                required = "필수" in widget.label.text()
                if required:
                    self.log(f"⚠️ {file_type}: 파일이 선택되지 않음")

        self.log("=== 파일 검증 완료 ===")

    def get_selected_months(self) -> list:
        """선택된 년월 반환"""
        year = self.year_combo.currentText()
        selected_months = []

        for month, checkbox in self.month_checkboxes.items():
            if checkbox.isChecked():
                selected_months.append(f"{year}{month:02d}")

        return selected_months

    def execute_reconciliation(self):
        """대사 실행"""
        selected_months = self.get_selected_months()
        if not selected_months:
            QMessageBox.warning(self, "경고", "최소 1개월 이상 선택해주세요.")
            return

        self.log(f"=== 대사 실행 시작 ===")
        self.log(f"선택된 기간: {', '.join(selected_months)}")

        # UI 비활성화
        self.btn_execute.setEnabled(False)
        self.btn_download.setEnabled(False)
        self.progress_bar.setVisible(True)

        # 스레드 실행
        self.thread = ReconciliationThread(self.file_paths, selected_months)
        self.thread.progress.connect(self.update_progress)
        self.thread.message.connect(self.log)
        self.thread.finished.connect(self.on_reconciliation_finished)
        self.thread.error.connect(self.on_reconciliation_error)
        self.thread.start()

    def on_reconciliation_finished(self, results: dict):
        """대사 완료"""
        self.current_results = results
        self.log("✅ 대사 완료!")

        # 결과 표시
        if 'reconciliation_result' in results:
            df = results['reconciliation_result']
            self.display_results(df)

            # 요약 표시
            if 'summary' in results:
                summary = results['summary']
                summary_text = f"총 {len(df)}건 처리\n"
                for _, row in summary.iterrows():
                    summary_text += f"{row['구분']}: {row['대사율']:.1f}%\n"
                self.summary_label.setText(summary_text)

        # UI 활성화
        self.btn_execute.setEnabled(True)
        self.btn_download.setEnabled(True)
        self.progress_bar.setVisible(False)

    def on_reconciliation_error(self, error_msg: str):
        """대사 오류"""
        self.log(f"❌ 오류: {error_msg}")
        QMessageBox.critical(self, "오류", error_msg)

        # UI 활성화
        self.btn_execute.setEnabled(True)
        self.progress_bar.setVisible(False)

    def display_results(self, df: pd.DataFrame):
        """결과 테이블에 표시"""
        self.result_table.setRowCount(len(df))
        self.result_table.setColumnCount(len(df.columns))
        self.result_table.setHorizontalHeaderLabels(df.columns.tolist())

        for row in range(len(df)):
            for col in range(len(df.columns)):
                value = df.iloc[row, col]
                if pd.isna(value):
                    item = QTableWidgetItem("")
                else:
                    item = QTableWidgetItem(str(value))
                self.result_table.setItem(row, col, item)

        self.result_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )

    def download_results(self):
        """결과 다운로드"""
        if not self.current_results:
            return

        # 저장 경로 선택
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"매입대사결과_{timestamp}.xlsx"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "결과 저장",
            default_name,
            "Excel Files (*.xlsx)"
        )

        if file_path:
            try:
                # 엑셀 파일로 저장
                with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                    for sheet_name, df in self.current_results.items():
                        if isinstance(df, pd.DataFrame) and not df.empty:
                            clean_name = sheet_name.replace('_', ' ').title()[:31]
                            df.to_excel(writer, sheet_name=clean_name, index=False)

                self.log(f"✅ 파일 저장 완료: {file_path}")

                # 파일 열기 옵션
                reply = QMessageBox.question(
                    self,
                    "저장 완료",
                    "파일이 저장되었습니다. 파일을 여시겠습니까?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.Yes:
                    import os
                    os.startfile(file_path)

            except Exception as e:
                QMessageBox.critical(self, "오류", f"저장 실패: {str(e)}")

    def update_progress(self, value: int):
        """진행률 업데이트"""
        self.progress_bar.setValue(value)

    def log(self, message: str):
        """로그 메시지 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

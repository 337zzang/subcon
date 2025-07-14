from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QGroupBox,
    QFileDialog, QMessageBox, QProgressBar, QTableWidget,
    QTableWidgetItem, QTextEdit, QSplitter, QHeaderView, QDateEdit,
    QDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer, QDate, QSettings
from PyQt6.QtGui import QFont, QPalette, QColor
import pandas as pd
from typing import Dict, Optional
from pathlib import Path
from datetime import datetime
import json
import sys
import os

# kfunction 모듈 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from kfunction import read_excel_data

from src.services.excel_service import ExcelService
from ..services.reconciliation_service_v2 import ReconciliationService
from .workers.reconciliation_worker import ReconciliationWorker
from .widgets.progress_dialog import ProgressDialog

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
        # 부모 윈도우에서 기본 폴더 가져오기
        default_folder = ""
        if hasattr(self.window(), 'upload_folder'):
            default_folder = self.window().upload_folder
            
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"{self.label.text()} 선택",
            default_folder,
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
            # kfunction의 read_excel_data 사용 (첫 5행만 읽어서 검증)
            df = read_excel_data(self.file_path)
            if len(df) > 5:
                df = df.head(5)  # 검증용으로 5행만 확인
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

        

class ImprovedMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.file_paths = {}
        self.current_results = None
        
        # 설정 초기화
        self.settings = QSettings('SubconSystem', 'ReconciliationApp')
        self.upload_folder = self.settings.value('upload_folder', '')
        self.download_folder = self.settings.value('download_folder', '')
        
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
        
        # 설정 로드 확인
        if self.upload_folder or self.download_folder:
            self.log("📁 기본 폴더 설정이 로드되었습니다.")
            if self.upload_folder:
                self.log(f"  - 업로드: {self.upload_folder}")
            if self.download_folder:
                self.log(f"  - 다운로드: {self.download_folder}")

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
            ('payment_ledger', '지불보조장 (필수)', True),
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

        # 날짜 선택
        date_layout = QHBoxLayout()
        
        # 오늘 날짜 기준으로 현재 연도 가져오기
        current_year = datetime.now().year
        
        # 시작일
        date_layout.addWidget(QLabel("시작일:"))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate(current_year, 1, 1))  # 현재 연도 1월 1일
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        self.start_date.dateChanged.connect(self.validate_dates)  # 날짜 변경 시 검증
        date_layout.addWidget(self.start_date)
        
        date_layout.addWidget(QLabel("~"))
        
        # 종료일
        date_layout.addWidget(QLabel("종료일:"))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate(current_year, 6, 30))  # 현재 연도 6월 30일
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        self.end_date.dateChanged.connect(self.validate_dates)  # 날짜 변경 시 검증
        date_layout.addWidget(self.end_date)
        
        date_layout.addStretch()
        period_layout.addLayout(date_layout)
        
        # 날짜 유효성 설명
        info_label = QLabel(f"* 대사 기간을 선택하세요 (기본값: {current_year}년 전반기)")
        info_label.setStyleSheet("color: #666; font-size: 11px;")
        period_layout.addWidget(info_label)
        
        period_group.setLayout(period_layout)
        layout.addWidget(period_group)

        # 3. 실행 버튼
        execute_group = QGroupBox("⚡ 실행")
        execute_layout = QVBoxLayout()
        
        # 설정 버튼
        self.btn_settings = QPushButton("⚙️ 기본 폴더 설정")
        self.btn_settings.clicked.connect(self.show_settings_dialog)
        execute_layout.addWidget(self.btn_settings)
        
        # 구분선
        execute_layout.addWidget(QLabel(""))

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
        required_files = ['supplier_purchase', 'standard', 'tax_invoice', 'tax_invoice_wis', 'payment_ledger']
        all_uploaded = all(f in self.file_paths for f in required_files)

        if all_uploaded:
            self.btn_execute.setEnabled(True)
            self.log("✅ 모든 필수 파일이 업로드되었습니다. 대사를 실행할 수 있습니다.")

    def validate_dates(self):
        """날짜 유효성 검사"""
        start_date = self.start_date.date()
        end_date = self.end_date.date()
        
        if start_date > end_date:
            QMessageBox.warning(
                self, 
                "날짜 오류", 
                "시작일이 종료일보다 늦을 수 없습니다.\n날짜를 다시 선택해주세요."
            )
            # 날짜를 원래대로 되돌림
            self.start_date.setDate(end_date.addDays(-1))
            
    def toggle_months(self, checked: bool):
        """더 이상 사용되지 않음 (날짜 선택으로 변경)"""
        pass

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
        """선택된 시작일/종료일 반환 (더 이상 월 기반이 아님)"""
        # 이 메서드는 호환성을 위해 유지하지만 날짜 기반으로 변경
        start_date = self.start_date.date().toPyDate()
        end_date = self.end_date.date().toPyDate()
        
        # 유효성 검사
        if start_date > end_date:
            return []
            
        # 날짜 정보를 리스트로 반환 (기존 코드와의 호환성을 위해)
        return [start_date, end_date]

    def execute_reconciliation(self):
        """대사 실행"""
        period = self.get_selected_months()  # 날짜 정보 가져오기
        if not period or len(period) != 2:
            QMessageBox.warning(self, "경고", "대사 기간을 선택해주세요.")
            return
            
        start_date, end_date = period
        
        # 날짜 유효성 검사 (한번 더 확인)
        if start_date > end_date:
            QMessageBox.critical(
                self, 
                "날짜 오류", 
                f"시작일({start_date.strftime('%Y-%m-%d')})이 종료일({end_date.strftime('%Y-%m-%d')})보다 늦습니다.\n"
                "날짜를 다시 선택해주세요."
            )
            return

        self.log(f"=== 대사 실행 시작 ===")
        self.log(f"선택된 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")

        # 진행률 다이얼로그 표시
        self.progress_dialog = ProgressDialog(self, "매입대사 처리 중")
        self.progress_dialog.show()

        # UI 비활성화
        self.btn_execute.setEnabled(False)
        self.btn_download.setEnabled(False)

        # 스레드 실행
        self.thread = ReconciliationWorker(self.file_paths, start_date, end_date)
        self.thread.progress.connect(self.progress_dialog.update_progress)
        self.thread.message.connect(self.progress_dialog.append_message)
        self.thread.message.connect(self.log)
        self.thread.finished.connect(self.on_reconciliation_finished)
        self.thread.error.connect(self.on_reconciliation_error)
        
        # 다이얼로그 취소 버튼 연결
        self.progress_dialog.canceled.connect(self.thread.stop)
        
        self.thread.start()

    def on_reconciliation_finished(self, results: dict):
        """대사 완료"""
        self.current_results = results
        self.log("✅ 대사 완료!")
        
        # 진행률 다이얼로그 완료 처리
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.on_finished()

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
        
        # 진행률 다이얼로그 오류 처리
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.on_error(error_msg)
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
        
        # 기본 다운로드 폴더 설정
        default_path = default_name
        if self.download_folder:
            default_path = str(Path(self.download_folder) / default_name)

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "결과 저장",
            default_path,
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
        
    def show_settings_dialog(self):
        """설정 다이얼로그 표시"""
        dialog = SettingsDialog(self, self.upload_folder, self.download_folder)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.upload_folder = dialog.upload_folder
            self.download_folder = dialog.download_folder
            
            # 설정 저장
            self.settings.setValue('upload_folder', self.upload_folder)
            self.settings.setValue('download_folder', self.download_folder)
            
            self.log(f"✅ 설정이 저장되었습니다.")
            self.log(f"  - 업로드 폴더: {self.upload_folder or '(미설정)'}")
            self.log(f"  - 다운로드 폴더: {self.download_folder or '(미설정)'}")


class SettingsDialog(QDialog):
    """설정 다이얼로그"""
    
    def __init__(self, parent=None, upload_folder='', download_folder=''):
        super().__init__(parent)
        self.upload_folder = upload_folder
        self.download_folder = download_folder
        self.init_ui()
        
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("기본 폴더 설정")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        
        # 설명
        info_label = QLabel("파일 업로드와 다운로드의 기본 폴더를 설정합니다.")
        info_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(info_label)
        
        # 업로드 폴더 설정
        upload_group = QGroupBox("파일 업로드 기본 폴더")
        upload_layout = QHBoxLayout()
        
        self.upload_edit = QLineEdit(self.upload_folder)
        self.upload_edit.setPlaceholderText("업로드할 파일의 기본 위치")
        upload_layout.addWidget(self.upload_edit)
        
        upload_btn = QPushButton("찾아보기...")
        upload_btn.clicked.connect(self.select_upload_folder)
        upload_layout.addWidget(upload_btn)
        
        upload_group.setLayout(upload_layout)
        layout.addWidget(upload_group)
        
        # 다운로드 폴더 설정
        download_group = QGroupBox("결과 다운로드 기본 폴더")
        download_layout = QHBoxLayout()
        
        self.download_edit = QLineEdit(self.download_folder)
        self.download_edit.setPlaceholderText("결과 파일을 저장할 기본 위치")
        download_layout.addWidget(self.download_edit)
        
        download_btn = QPushButton("찾아보기...")
        download_btn.clicked.connect(self.select_download_folder)
        download_layout.addWidget(download_btn)
        
        download_group.setLayout(download_layout)
        layout.addWidget(download_group)
        
        # 버튼
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
    def select_upload_folder(self):
        """업로드 폴더 선택"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "업로드 기본 폴더 선택",
            self.upload_edit.text() or ""
        )
        if folder:
            self.upload_edit.setText(folder)
            
    def select_download_folder(self):
        """다운로드 폴더 선택"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "다운로드 기본 폴더 선택",
            self.download_edit.text() or ""
        )
        if folder:
            self.download_edit.setText(folder)
            
    def accept(self):
        """확인 버튼 클릭"""
        self.upload_folder = self.upload_edit.text()
        self.download_folder = self.download_edit.text()
        super().accept()

"""
메인 윈도우 UI
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem,
    QLabel, QProgressBar, QGroupBox, QTextEdit,
    QFileDialog, QMessageBox, QSplitter, QHeaderView,
    QTabWidget, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QAction, QIcon
import pandas as pd
from typing import Optional, Dict
import json
from pathlib import Path
from datetime import datetime

from src.services.excel_service import ExcelService
from src.services.reconciliation_service import ReconciliationService
from src.ui.widgets.analysis_widget import AnalysisWidget

class DataProcessThread(QThread):
    """데이터 처리를 위한 별도 스레드"""
    progress = pyqtSignal(int)
    message = pyqtSignal(str)
    finished = pyqtSignal(dict)  # DataFrame 대신 dict로 변경
    error = pyqtSignal(str)
    
    def __init__(self, reconciliation_service: ReconciliationService, config: dict):
        super().__init__()
        self.reconciliation_service = reconciliation_service
        self.config = config
        
    def run(self):
        try:
            self.message.emit("대사 프로세스 시작...")
            self.progress.emit(10)
            
            # 전체 대사 프로세스 실행
            results = self.reconciliation_service.process_all_reconciliation(self.config)
            
            self.progress.emit(100)
            self.message.emit("대사 프로세스 완료!")
            self.finished.emit(results)
            
        except Exception as e:
            self.error.emit(f"처리 중 오류 발생: {str(e)}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.excel_service = ExcelService()
        self.reconciliation_service = ReconciliationService(self.excel_service)
        self.current_results: Optional[Dict[str, pd.DataFrame]] = None
        self.config = self.load_config()
        
        self.init_ui()
        
    def load_config(self) -> dict:
        """설정 파일 로드"""
        config_path = Path("config/app_config.json")
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
        
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle(self.config.get('app_name', '협력사 매입대사 시스템'))
        self.setGeometry(100, 100, 
                        self.config['window']['width'], 
                        self.config['window']['height'])
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(central_widget)
        
        # 툴바 영역
        toolbar_layout = QHBoxLayout()
        
        # 실행 버튼들
        self.btn_load_data = QPushButton("📂 데이터 확인")
        self.btn_load_data.clicked.connect(self.check_data_files)
        
        self.btn_process = QPushButton("⚙️ 매입대사 실행")
        self.btn_process.clicked.connect(self.process_reconciliation)
        self.btn_process.setEnabled(False)
        
        self.btn_export = QPushButton("💾 결과 저장")
        self.btn_export.clicked.connect(self.save_results)
        self.btn_export.setEnabled(False)
        
        # 출력 폴더 선택
        self.lbl_output = QLabel("출력 폴더:")
        self.combo_output = QComboBox()
        self.combo_output.addItem("OUT (기본)")
        self.combo_output.addItem("선택...")
        self.combo_output.currentTextChanged.connect(self.on_output_folder_changed)
        
        toolbar_layout.addWidget(self.btn_load_data)
        toolbar_layout.addWidget(self.btn_process)
        toolbar_layout.addWidget(self.btn_export)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.lbl_output)
        toolbar_layout.addWidget(self.combo_output)
        
        main_layout.addLayout(toolbar_layout)
        
        # 탭 위젯
        self.tab_widget = QTabWidget()
        
        # 데이터 탭
        self.data_tab = QWidget()
        data_layout = QVBoxLayout(self.data_tab)
        
        # 데이터 테이블
        self.data_table = QTableWidget()
        data_layout.addWidget(self.data_table)
        
        # 로그 탭
        self.log_tab = QWidget()
        log_layout = QVBoxLayout(self.log_tab)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        # 분석 탭
        self.analysis_widget = AnalysisWidget()
        self.analysis_widget.refresh_requested.connect(self.process_reconciliation)
        
        # 탭 추가
        self.tab_widget.addTab(self.data_tab, "데이터")
        self.tab_widget.addTab(self.analysis_widget, "분석")
        self.tab_widget.addTab(self.log_tab, "로그")
        
        main_layout.addWidget(self.tab_widget)
        
        # 상태바
        self.status_bar = self.statusBar()
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # 메뉴바
        self.create_menu_bar()
        
        # 기본 출력 폴더
        self.output_folder = "OUT"
        
    def create_menu_bar(self):
        """메뉴바 생성"""
        menubar = self.menuBar()
        
        # 파일 메뉴
        file_menu = menubar.addMenu("파일")
        
        exit_action = QAction("종료", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 도움말 메뉴
        help_menu = menubar.addMenu("도움말")
        
        about_action = QAction("정보", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def check_data_files(self):
        """데이터 파일 확인"""
        self.log("데이터 파일 확인 중...")
        
        # 필요한 파일들 확인
        missing_files = []
        file_status = []
        
        for key, filename in self.config['excel_files'].items():
            file_path = Path(f"data/{filename}")
            if file_path.exists():
                file_status.append(f"✅ {filename}")
            else:
                missing_files.append(filename)
                file_status.append(f"❌ {filename}")
                
        # 상태 표시
        for status in file_status:
            self.log(status)
                
        if missing_files:
            QMessageBox.warning(
                self,
                "파일 누락",
                f"다음 파일들이 없습니다:\n{chr(10).join(missing_files)}"
            )
        else:
            self.log("모든 데이터 파일이 확인되었습니다.")
            self.btn_process.setEnabled(True)
            
    def on_output_folder_changed(self, text):
        """출력 폴더 변경"""
        if text == "선택...":
            folder = QFileDialog.getExistingDirectory(self, "출력 폴더 선택")
            if folder:
                self.output_folder = folder
                self.combo_output.insertItem(1, folder)
                self.combo_output.setCurrentIndex(1)
            else:
                self.combo_output.setCurrentIndex(0)
        elif text == "OUT (기본)":
            self.output_folder = "OUT"
        else:
            self.output_folder = text
            
        self.log(f"출력 폴더 설정: {self.output_folder}")
        
    def process_reconciliation(self):
        """대사 프로세스 실행"""
        self.btn_process.setEnabled(False)
        self.btn_export.setEnabled(False)
        self.progress_bar.setVisible(True)
        
        # 별도 스레드에서 처리
        self.process_thread = DataProcessThread(self.reconciliation_service, self.config)
        self.process_thread.progress.connect(self.update_progress)
        self.process_thread.message.connect(self.log)
        self.process_thread.finished.connect(self.on_process_finished)
        self.process_thread.error.connect(self.on_process_error)
        self.process_thread.start()
        
    def on_process_finished(self, results: Dict[str, pd.DataFrame]):
        """처리 완료"""
        self.current_results = results
        
        # 메인 결과 표시
        if 'reconciliation_result' in results:
            df = results['reconciliation_result']
            self.display_data(df)
            self.log(f"처리 완료! 총 {len(df)}개 항목")
            
            # 요약 정보 표시
            if 'summary' in results:
                summary = results['summary']
                self.log("\n=== 대사 요약 ===")
                for _, row in summary.iterrows():
                    self.log(f"{row['구분']}: 대사율 {row['대사율']:.1f}%")
        
        # 분석 위젯에 DataManager 연결
        data_manager = self.excel_service.get_data_manager()
        self.analysis_widget.set_data_manager(data_manager)
        
        self.btn_export.setEnabled(True)
        self.btn_process.setEnabled(True)
        self.progress_bar.setVisible(False)
        
    def on_process_error(self, error_msg: str):
        """처리 오류"""
        self.log(f"❌ {error_msg}")
        self.btn_process.setEnabled(True)
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "오류", error_msg)
        
    def display_data(self, df: pd.DataFrame):
        """데이터 테이블에 표시"""
        self.data_table.setRowCount(len(df))
        self.data_table.setColumnCount(len(df.columns))
        self.data_table.setHorizontalHeaderLabels(df.columns.tolist())
        
        for row in range(len(df)):
            for col in range(len(df.columns)):
                value = df.iloc[row, col]
                # None이나 pd.NaT 처리
                if pd.isna(value):
                    item = QTableWidgetItem("")
                else:
                    item = QTableWidgetItem(str(value))
                self.data_table.setItem(row, col, item)
                
        # 컬럼 너비 자동 조정
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
    def save_results(self):
        """결과 저장"""
        if not self.current_results:
            return
            
        try:
            # ReconciliationService의 결과 설정
            self.reconciliation_service.reconciliation_results = self.current_results
            
            # 저장
            saved_file = self.reconciliation_service.save_results(self.output_folder)
            
            self.log(f"✅ 결과 저장 완료: {saved_file}")
            
            # 폴더 열기 옵션
            reply = QMessageBox.question(
                self, 
                "저장 완료", 
                f"결과가 저장되었습니다.\n폴더를 여시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                import os
                os.startfile(self.output_folder)
                
        except Exception as e:
            QMessageBox.critical(self, "오류", f"저장 실패: {str(e)}")
            
    def update_progress(self, value: int):
        """진행률 업데이트"""
        self.progress_bar.setValue(value)
        
    def log(self, message: str):
        """로그 메시지 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
    def show_about(self):
        """프로그램 정보"""
        QMessageBox.about(
            self,
            "정보",
            f"{self.config.get('app_name', '협력사 매입대사 시스템')}\n"
            f"버전: {self.config.get('version', '1.0.0')}\n\n"
            "협력사별 매입 데이터를 처리하고 세금계산서와 대사하는 프로그램입니다.\n\n"
            "주요 기능:\n"
            "- 매입데이터와 세금계산서 자동 대사\n"
            "- 금액대사, 순차대사, 부분대사 지원\n"
            "- 대사 결과 엑셀 저장"
        )

"""
진행률 표시 다이얼로그
"""
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QTextEdit, QPushButton, QDialogButtonBox
from PyQt6.QtCore import Qt, pyqtSignal


class ProgressDialog(QDialog):
    """작업 진행률을 표시하는 다이얼로그"""
    
    canceled = pyqtSignal()
    
    def __init__(self, parent=None, title="작업 진행 중"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setMinimumHeight(300)
        
        # 윈도우 플래그 설정 - 닫기 버튼 비활성화
        self.setWindowFlags(
            Qt.WindowType.Dialog | 
            Qt.WindowType.WindowTitleHint | 
            Qt.WindowType.CustomizeWindowHint
        )
        
        self.init_ui()
        
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        
        # 상태 레이블
        self.status_label = QLabel("준비 중...")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.status_label)
        
        # 진행률 바
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        # 상세 메시지
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setMaximumHeight(150)
        self.detail_text.setStyleSheet("background-color: #f5f5f5;")
        layout.addWidget(self.detail_text)
        
        # 버튼
        self.button_box = QDialogButtonBox()
        self.cancel_button = QPushButton("취소")
        self.cancel_button.clicked.connect(self.on_cancel)
        self.button_box.addButton(self.cancel_button, QDialogButtonBox.ButtonRole.RejectRole)
        
        self.close_button = QPushButton("닫기")
        self.close_button.clicked.connect(self.accept)
        self.close_button.setEnabled(False)  # 처음에는 비활성화
        self.button_box.addButton(self.close_button, QDialogButtonBox.ButtonRole.AcceptRole)
        
        layout.addWidget(self.button_box)
        
        self.setLayout(layout)
        
    def update_progress(self, value: int):
        """진행률 업데이트"""
        self.progress_bar.setValue(value)
        
    def update_status(self, message: str):
        """상태 메시지 업데이트"""
        self.status_label.setText(message)
        
    def append_message(self, message: str):
        """상세 메시지 추가"""
        self.detail_text.append(message)
        # 자동 스크롤
        scrollbar = self.detail_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def on_cancel(self):
        """취소 버튼 클릭"""
        self.canceled.emit()
        self.cancel_button.setEnabled(False)
        self.cancel_button.setText("취소 중...")
        
    def on_finished(self):
        """작업 완료 시"""
        self.cancel_button.setEnabled(False)
        self.close_button.setEnabled(True)
        self.status_label.setText("✅ 작업 완료!")
        
    def on_error(self, error_msg: str):
        """오류 발생 시"""
        self.cancel_button.setEnabled(False)
        self.close_button.setEnabled(True)
        self.status_label.setText("❌ 오류 발생!")
        self.status_label.setStyleSheet("color: red; font-size: 14px; font-weight: bold;")
        self.append_message(f"\n오류: {error_msg}")

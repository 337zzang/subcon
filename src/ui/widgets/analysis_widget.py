"""
데이터 분석 위젯
매입 데이터 요약 및 통계 표시
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QGroupBox,
    QComboBox, QPushButton, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from typing import Optional
from decimal import Decimal

from ...services.data_manager import DataManager

class AnalysisWidget(QWidget):
    """데이터 분석 위젯"""

    refresh_requested = pyqtSignal()

    def __init__(self, data_manager: Optional[DataManager] = None):
        super().__init__()
        self.data_manager = data_manager
        self.init_ui()

    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()

        # 제목
        title = QLabel("📊 매입 데이터 분석")
        title.setFont(QFont("맑은 고딕", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        # 필터 영역
        filter_layout = QHBoxLayout()

        # 년월 선택
        filter_layout.addWidget(QLabel("년월:"))
        self.month_combo = QComboBox()
        self.month_combo.currentTextChanged.connect(self.update_display)
        filter_layout.addWidget(self.month_combo)

        # 협력사 선택
        filter_layout.addWidget(QLabel("협력사:"))
        self.supplier_combo = QComboBox()
        self.supplier_combo.addItem("전체")
        self.supplier_combo.currentTextChanged.connect(self.update_display)
        filter_layout.addWidget(self.supplier_combo)

        # 새로고침 버튼
        self.btn_refresh = QPushButton("🔄 새로고침")
        self.btn_refresh.clicked.connect(self.refresh_requested.emit)
        filter_layout.addWidget(self.btn_refresh)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # 요약 정보
        self.summary_group = QGroupBox("요약 정보")
        summary_layout = QVBoxLayout()

        # 요약 레이블들
        self.lbl_total_amount = QLabel("총 매입금액: 0원")
        self.lbl_taxable_amount = QLabel("과세: 0원")
        self.lbl_tax_free_amount = QLabel("면세: 0원")
        self.lbl_supplier_count = QLabel("협력사 수: 0")

        summary_layout.addWidget(self.lbl_total_amount)
        summary_layout.addWidget(self.lbl_taxable_amount)
        summary_layout.addWidget(self.lbl_tax_free_amount)
        summary_layout.addWidget(self.lbl_supplier_count)

        self.summary_group.setLayout(summary_layout)
        layout.addWidget(self.summary_group)

        # 상세 테이블
        self.detail_table = QTableWidget()
        self.detail_table.setColumnCount(5)
        self.detail_table.setHorizontalHeaderLabels([
            "년월", "협력사코드", "협력사명", "구분", "금액"
        ])
        self.detail_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        layout.addWidget(self.detail_table)

        self.setLayout(layout)

    def set_data_manager(self, data_manager: DataManager):
        """DataManager 설정"""
        self.data_manager = data_manager
        self.update_filters()
        self.update_display()

    def update_filters(self):
        """필터 콤보박스 업데이트"""
        if not self.data_manager:
            return

        # 년월 목록 업데이트
        months = set()
        for summary in self.data_manager.purchase_summaries.values():
            months.add(summary.year_month)

        self.month_combo.clear()
        self.month_combo.addItem("전체")
        for month in sorted(months):
            self.month_combo.addItem(month)

        # 협력사 목록 업데이트
        self.supplier_combo.clear()
        self.supplier_combo.addItem("전체")
        for code, supplier in sorted(self.data_manager.suppliers.items()):
            self.supplier_combo.addItem(f"{supplier.supplier_name} ({code})")

    def update_display(self):
        """화면 업데이트"""
        if not self.data_manager:
            return

        selected_month = self.month_combo.currentText()
        selected_supplier = self.supplier_combo.currentText()

        # 필터링
        filtered_summaries = []
        for summary in self.data_manager.purchase_summaries.values():
            # 월 필터
            if selected_month != "전체" and summary.year_month != selected_month:
                continue

            # 협력사 필터
            if selected_supplier != "전체":
                supplier_code = selected_supplier.split("(")[-1].rstrip(")")
                if summary.supplier_code != supplier_code:
                    continue

            filtered_summaries.append(summary)

        # 요약 정보 계산
        total_amount = Decimal('0')
        taxable_amount = Decimal('0')
        tax_free_amount = Decimal('0')
        suppliers = set()

        for summary in filtered_summaries:
            total_amount += summary.total_amount
            if summary.tax_type == "과세":
                taxable_amount += summary.total_amount
            else:
                tax_free_amount += summary.total_amount
            suppliers.add(summary.supplier_code)

        # 요약 레이블 업데이트
        self.lbl_total_amount.setText(f"총 매입금액: {total_amount:,.0f}원")
        self.lbl_taxable_amount.setText(f"과세: {taxable_amount:,.0f}원")
        self.lbl_tax_free_amount.setText(f"면세: {tax_free_amount:,.0f}원")
        self.lbl_supplier_count.setText(f"협력사 수: {len(suppliers)}")

        # 테이블 업데이트
        self.detail_table.setRowCount(len(filtered_summaries))
        for row, summary in enumerate(filtered_summaries):
            self.detail_table.setItem(row, 0, QTableWidgetItem(summary.year_month))
            self.detail_table.setItem(row, 1, QTableWidgetItem(summary.supplier_code))
            self.detail_table.setItem(row, 2, QTableWidgetItem(summary.supplier_name))
            self.detail_table.setItem(row, 3, QTableWidgetItem(summary.tax_type))

            # 금액은 우측 정렬
            amount_item = QTableWidgetItem(f"{summary.total_amount:,.0f}")
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.detail_table.setItem(row, 4, amount_item)

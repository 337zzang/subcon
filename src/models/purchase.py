"""
매입 데이터 모델
"""
from dataclasses import dataclass, field
from typing import Optional
from decimal import Decimal
from datetime import date
from .base_model import BaseModel

@dataclass
class Purchase(BaseModel):
    """매입 데이터"""
    year_month: str              # 년월 (YYYYMM)
    supplier_code: str           # 협력사코드
    supplier_name: str           # 협력사명
    product_code: str            # 단품코드
    product_name: str            # 단품명
    tax_type: str               # 면과세구분명 (과세/면세)
    purchase_quantity: Decimal = Decimal('0')     # 매입확정수량
    discount_amount: Decimal = Decimal('0')       # 매입에누리금액
    incentive_amount: Decimal = Decimal('0')      # 매입장려금금액
    adjustment_amount: Decimal = Decimal('0')     # 매입조정금액
    purchase_amount: Decimal = Decimal('0')       # 매입금액
    final_amount: Decimal = Decimal('0')          # 최종매입금액

    def __post_init__(self):
        """초기화 후 처리"""
        self.supplier_code = str(self.supplier_code)
        self.product_code = str(self.product_code)

        # Decimal 변환
        self.purchase_quantity = Decimal(str(self.purchase_quantity))
        self.discount_amount = Decimal(str(self.discount_amount))
        self.incentive_amount = Decimal(str(self.incentive_amount))
        self.adjustment_amount = Decimal(str(self.adjustment_amount))
        self.purchase_amount = Decimal(str(self.purchase_amount))
        self.final_amount = Decimal(str(self.final_amount))

    @property
    def year(self) -> int:
        """연도"""
        return int(self.year_month[:4])

    @property
    def month(self) -> int:
        """월"""
        return int(self.year_month[4:6])

    @property
    def key(self) -> str:
        """고유 키 (년월+협력사코드+면과세구분)"""
        return f"{self.year_month}{self.supplier_code}{self.tax_type}"

    def calculate_final_amount(self) -> Decimal:
        """최종매입금액 계산"""
        return (self.purchase_amount - self.discount_amount + 
                self.incentive_amount + self.adjustment_amount)

@dataclass
class PurchaseSummary(BaseModel):
    """매입 집계 데이터"""
    year_month: str
    supplier_code: str
    supplier_name: str
    tax_type: str
    total_amount: Decimal = Decimal('0')
    count: int = 0

    def __post_init__(self):
        """초기화 후 처리"""
        self.supplier_code = str(self.supplier_code)
        self.total_amount = Decimal(str(self.total_amount))

    @property
    def key(self) -> str:
        """고유 키"""
        return f"{self.year_month}{self.supplier_code}{self.tax_type}"

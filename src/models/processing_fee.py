"""
임가공비 데이터 모델
"""
from dataclasses import dataclass
from decimal import Decimal
from datetime import date
from typing import Optional
from .base_model import BaseModel

@dataclass
class ProcessingFee(BaseModel):
    """임가공비 정보"""
    year_month: str             # 년월
    supplier_code: str          # 협력사코드
    supplier_name: str          # 협력사명
    product_code: str           # 단품코드
    product_name: str           # 단품명
    quantity: Decimal = Decimal('0')        # 수량
    unit_price: Decimal = Decimal('0')      # 단가
    amount: Decimal = Decimal('0')          # 금액
    tax_type: str = "과세"                  # 과세구분
    description: Optional[str] = None       # 비고

    def __post_init__(self):
        """초기화 후 처리"""
        self.supplier_code = str(self.supplier_code)
        self.product_code = str(self.product_code)
        self.quantity = Decimal(str(self.quantity))
        self.unit_price = Decimal(str(self.unit_price))
        self.amount = Decimal(str(self.amount))

    def calculate_amount(self) -> Decimal:
        """금액 계산"""
        return self.quantity * self.unit_price

    @property
    def key(self) -> str:
        """고유 키"""
        return f"{self.year_month}{self.supplier_code}{self.product_code}"

"""
지불 데이터 모델
"""
from dataclasses import dataclass, field
from typing import Optional, List
from decimal import Decimal
from datetime import date
from .base_model import BaseModel

@dataclass
class Payment(BaseModel):
    """지불 정보"""
    payment_date: date          # 지불일자
    supplier_code: str          # 협력사코드
    supplier_name: str          # 협력사명
    payment_type: str          # 지불유형 (현금/어음/계좌이체 등)
    amount: Decimal            # 지불금액
    reference_number: Optional[str] = None    # 참조번호 (전표번호 등)
    bank_name: Optional[str] = None          # 은행명
    account_number: Optional[str] = None     # 계좌번호
    description: Optional[str] = None        # 적요/비고
    status: str = "completed"               # 상태

    def __post_init__(self):
        """초기화 후 처리"""
        self.supplier_code = str(self.supplier_code)
        self.amount = Decimal(str(self.amount))

        # 날짜 변환
        if isinstance(self.payment_date, str):
            self.payment_date = date.fromisoformat(self.payment_date)

    @property
    def year_month(self) -> str:
        """년월 (YYYYMM)"""
        return self.payment_date.strftime("%Y%m")

@dataclass
class PaymentLedger(BaseModel):
    """지불보조장"""
    year_month: str             # 년월
    supplier_code: str          # 협력사코드
    supplier_name: str          # 협력사명
    previous_balance: Decimal = Decimal('0')    # 전월이월
    purchase_amount: Decimal = Decimal('0')     # 당월매입
    payment_amount: Decimal = Decimal('0')      # 당월지불
    current_balance: Decimal = Decimal('0')     # 당월잔액

    def __post_init__(self):
        """초기화 후 처리"""
        self.supplier_code = str(self.supplier_code)
        self.previous_balance = Decimal(str(self.previous_balance))
        self.purchase_amount = Decimal(str(self.purchase_amount))
        self.payment_amount = Decimal(str(self.payment_amount))
        self.current_balance = Decimal(str(self.current_balance))

    def calculate_balance(self) -> Decimal:
        """잔액 계산"""
        return self.previous_balance + self.purchase_amount - self.payment_amount

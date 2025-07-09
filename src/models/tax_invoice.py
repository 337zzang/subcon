"""
세금계산서 데이터 모델
"""
from dataclasses import dataclass, field
from typing import Optional, List
from decimal import Decimal
from datetime import date
from .base_model import BaseModel

@dataclass
class TaxInvoice(BaseModel):
    """세금계산서 정보"""
    invoice_number: str          # 계산서번호
    invoice_date: date          # 발행일자
    supplier_code: str          # 협력사코드
    supplier_name: str          # 협력사명
    business_number: str        # 사업자번호
    tax_type: str              # 과세구분
    supply_amount: Decimal = Decimal('0')     # 공급가액
    tax_amount: Decimal = Decimal('0')        # 세액
    total_amount: Decimal = Decimal('0')      # 합계금액
    description: Optional[str] = None         # 품목/비고
    is_electronic: bool = True               # 전자세금계산서 여부
    status: str = "issued"                   # 상태 (issued/cancelled)

    def __post_init__(self):
        """초기화 후 처리"""
        self.supplier_code = str(self.supplier_code)
        self.supply_amount = Decimal(str(self.supply_amount))
        self.tax_amount = Decimal(str(self.tax_amount))
        self.total_amount = Decimal(str(self.total_amount))

        # 날짜 변환
        if isinstance(self.invoice_date, str):
            self.invoice_date = date.fromisoformat(self.invoice_date)

    def calculate_total(self) -> Decimal:
        """합계 계산"""
        return self.supply_amount + self.tax_amount

    @property
    def year_month(self) -> str:
        """년월 (YYYYMM)"""
        return self.invoice_date.strftime("%Y%m")

@dataclass
class TaxInvoiceWIS(TaxInvoice):
    """WIS 세금계산서 (상속)"""
    wis_number: Optional[str] = None      # WIS 관리번호
    department: Optional[str] = None      # 부서
    approval_status: str = "pending"      # 승인상태

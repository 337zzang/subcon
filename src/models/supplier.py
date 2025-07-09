"""
협력사 데이터 모델
"""
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from .base_model import BaseModel

@dataclass
class Supplier:
    """협력사 정보"""
    supplier_code: str          # 협력사코드
    supplier_name: str          # 협력사명
    business_number: Optional[str] = None  # 사업자번호
    address: Optional[str] = None          # 주소
    contact: Optional[str] = None          # 연락처
    email: Optional[str] = None            # 이메일
    tax_type: str = "과세"                 # 과세구분 (과세/면세)
    is_active: bool = True                 # 활성 상태
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """초기화 후 처리"""
        # 협력사코드를 문자열로 변환
        self.supplier_code = str(self.supplier_code)

    def __str__(self) -> str:
        return f"{self.supplier_name} ({self.supplier_code})"

    @property
    def display_name(self) -> str:
        """표시용 이름"""
        return f"[{self.supplier_code}] {self.supplier_name}"

@dataclass
class SupplierProduct(BaseModel):
    """협력사-단품 연결 정보"""
    supplier_code: str
    product_code: str
    product_name: str
    is_active: bool = True

    def __post_init__(self):
        """초기화 후 처리"""
        self.supplier_code = str(self.supplier_code)
        self.product_code = str(self.product_code)

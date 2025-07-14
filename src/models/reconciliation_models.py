"""
매입대사 시스템 데이터 모델
매입대사2.ipynb의 데이터 구조를 반영한 모델
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class PurchaseDetail:
    """협력사단품별매입 데이터"""
    년월: float
    협력사코드: str
    협력사명: str
    단품코드: str
    단품명: str
    면과세구분명: str
    매입확정수량: float
    매입에누리금액: float
    매입장려금금액: float
    매입조정금액: float
    매입금액: float
    최종매입금액: float


@dataclass
class Standard:
    """기준 데이터"""
    협력사코드: str
    협력사명: str
    단품코드: str
    단품명: str


@dataclass
class TaxInvoice:
    """매입세금계산서 데이터"""
    국세청승인번호: str
    업체사업자번호: str
    국세청작성일: datetime
    국세청발급일: datetime


@dataclass
class PaymentBook:
    """지불보조장 데이터"""
    계정코드: str
    계정과목명: str
    회계일: datetime
    전표유형: str
    회계단위: str
    전표번호: str
    확정번호: int
    전표상태: str
    증빙순번: int
    라인번호: int
    거래처번호: str
    거래처명: str
    차변금액: float
    대변금액: float


@dataclass
class TaxInvoiceWIS:
    """매입세금계산서(WIS) 데이터"""
    센터: str
    협력사승인여부: str
    계산서구분: str
    계산서작성일: datetime
    협력사코드: str
    협력사명: str
    협력사EMAIL: Optional[str]
    발행구분: str
    접수발행: str
    계산서상태: str
    사업자번호: str
    공급가액: float
    세액: float
    총액: float
    매입번호: str
    담당자사번: str
    담당자명: str
    HIVS승인번호: str
    국세청승인번호: str
    HIVS상태: Optional[str]
    국세청전송결과: Optional[str]
    회계확정여부: str
    협력사HP: Optional[str]


@dataclass
class ProcessingFee:
    """임가공비 데이터"""
    협력사코드: str
    협력사명: str
    금액: float
    년월: str


@dataclass
class ReconciliationResult:
    """대사 결과 데이터"""
    # 기본 정보
    년월: float
    협력사코드: str
    협력사명: str
    면과세구분명: str
    최종매입금액: float
    
    # 대사 정보
    구분키: Optional[str]
    key: str
    업체사업자번호: Optional[str]
    
    # 국세청 정보
    국세청작성일: Optional[datetime]
    국세청발급일: Optional[datetime]
    국세청공급가액: Optional[float]
    국세청세액: Optional[float]
    국세청승인번호: Optional[str]
    
    # 지불 정보
    최종지불금액: Optional[float]
    지불예상금액: Optional[float]
    
    # 기간별 합계
    합계_10일이하: Optional[float]
    합계_10초과_15일이하: Optional[float]
    합계_15초과_30일이하: Optional[float]
    합계_30일초과: Optional[float]
    
    # 차이 및 확인 정보
    차이내역: Optional[float]
    이전기간_지급: Optional[float]
    이후기간_지급: Optional[float]
    확인필요: Optional[float]


class DataContainer:
    """전체 데이터를 관리하는 컨테이너"""
    def __init__(self):
        self.purchase_details: List[PurchaseDetail] = []
        self.standards: List[Standard] = []
        self.tax_invoices: List[TaxInvoice] = []
        self.payment_books: List[PaymentBook] = []
        self.tax_invoices_wis: List[TaxInvoiceWIS] = []
        self.processing_fees: List[ProcessingFee] = []
        self.reconciliation_results: List[ReconciliationResult] = []
    
    def clear_all(self):
        """모든 데이터 초기화"""
        self.purchase_details.clear()
        self.standards.clear()
        self.tax_invoices.clear()
        self.payment_books.clear()
        self.tax_invoices_wis.clear()
        self.processing_fees.clear()
        self.reconciliation_results.clear()

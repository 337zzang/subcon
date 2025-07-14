"""
데이터 관리자 - 모든 데이터 모델을 통합 관리
"""
from typing import List, Dict, Optional, Tuple, Any
from decimal import Decimal
import pandas as pd
from collections import defaultdict
import os

from src.models import (
    Supplier, SupplierProduct, Purchase, PurchaseSummary,
    TaxInvoice, TaxInvoiceWIS, Payment, PaymentLedger,
    ProcessingFee
)

class DataManager:
    """데이터 통합 관리 클래스"""

    def __init__(self):
        # 데이터 저장소
        self.suppliers: Dict[str, Supplier] = {}
        self.supplier_products: List[SupplierProduct] = []
        self.purchases: List[Purchase] = []
        self.purchase_summaries: Dict[str, PurchaseSummary] = {}
        self.tax_invoices: List[TaxInvoice] = []
        self.tax_invoices_wis: List[TaxInvoiceWIS] = []
        self.payments: List[Payment] = []
        self.payment_ledgers: Dict[str, PaymentLedger] = {}
        self.processing_fees: List[ProcessingFee] = []
        
        # 파일 캐시 추가
        self._file_cache: Dict[str, pd.DataFrame] = {}

    def clear_all(self):
        """모든 데이터 초기화"""
        self.suppliers.clear()
        self.supplier_products.clear()
        self.purchases.clear()
        self.purchase_summaries.clear()
        self.tax_invoices.clear()
        self.tax_invoices_wis.clear()
        self.payments.clear()
        self.payment_ledgers.clear()
        self.processing_fees.clear()
        self._file_cache.clear()  # 파일 캐시도 초기화

    # 파일 캐싱 관련 메서드
    def cache_file_data(self, file_path: str, data: pd.DataFrame):
        """파일 데이터 캐싱"""
        normalized_path = os.path.normpath(file_path).lower()  # 경로 정규화
        self._file_cache[normalized_path] = data.copy()  # 데이터 복사본 저장
        
    def get_cached_data(self, file_path: str) -> Optional[pd.DataFrame]:
        """캐싱된 데이터 반환"""
        normalized_path = os.path.normpath(file_path).lower()
        return self._file_cache.get(normalized_path)
        
    def is_file_cached(self, file_path: str) -> bool:
        """파일이 캐싱되어 있는지 확인"""
        normalized_path = os.path.normpath(file_path).lower()
        return normalized_path in self._file_cache
        
    def clear_file_cache(self):
        """파일 캐시만 초기화"""
        self._file_cache.clear()
        
    def get_cache_size(self) -> int:
        """캐시된 파일 수 반환"""
        return len(self._file_cache)

    # 협력사 관련 메서드
    def add_supplier(self, supplier: Supplier):
        """협력사 추가"""
        self.suppliers[supplier.supplier_code] = supplier

    def get_supplier(self, supplier_code: str) -> Optional[Supplier]:
        """협력사 조회"""
        return self.suppliers.get(str(supplier_code))

    def load_suppliers_from_df(self, df: pd.DataFrame):
        """DataFrame에서 협력사 정보 로드"""
        unique_suppliers = df[['협력사코드', '협력사명']].drop_duplicates()

        for _, row in unique_suppliers.iterrows():
            supplier = Supplier(
                supplier_code=str(row['협력사코드']),
                supplier_name=row['협력사명']
            )
            self.add_supplier(supplier)

    # 매입 관련 메서드
    def add_purchase(self, purchase: Purchase):
        """매입 데이터 추가"""
        self.purchases.append(purchase)

    def load_purchases_from_df(self, df: pd.DataFrame):
        """DataFrame에서 매입 데이터 로드"""
        for _, row in df.iterrows():
            purchase = Purchase(
                year_month=str(int(row['년월'])),
                supplier_code=str(row['협력사코드']),
                supplier_name=row['협력사명'],
                product_code=str(row.get('단품코드', '')),
                product_name=row.get('단품명', ''),
                tax_type=row.get('면과세구분명', '과세'),
                purchase_quantity=Decimal(str(row.get('매입확정수량', 0))),
                discount_amount=Decimal(str(row.get('매입에누리금액', 0))),
                incentive_amount=Decimal(str(row.get('매입장려금금액', 0))),
                adjustment_amount=Decimal(str(row.get('매입조정금액', 0))),
                purchase_amount=Decimal(str(row.get('매입금액', 0))),
                final_amount=Decimal(str(row.get('최종매입금액', 0)))
            )
            self.add_purchase(purchase)

    def create_purchase_summary(self) -> Dict[str, PurchaseSummary]:
        """매입 데이터를 집계하여 요약 생성"""
        summary_dict = defaultdict(lambda: {
            'total_amount': Decimal('0'),
            'count': 0,
            'supplier_name': '',
            'tax_type': ''
        })

        for purchase in self.purchases:
            key = purchase.key
            summary_dict[key]['total_amount'] += purchase.final_amount
            summary_dict[key]['count'] += 1
            summary_dict[key]['supplier_name'] = purchase.supplier_name
            summary_dict[key]['tax_type'] = purchase.tax_type
            summary_dict[key]['year_month'] = purchase.year_month
            summary_dict[key]['supplier_code'] = purchase.supplier_code

        # PurchaseSummary 객체로 변환
        self.purchase_summaries.clear()
        for key, data in summary_dict.items():
            summary = PurchaseSummary(
                year_month=data['year_month'],
                supplier_code=data['supplier_code'],
                supplier_name=data['supplier_name'],
                tax_type=data['tax_type'],
                total_amount=data['total_amount'],
                count=data['count']
            )
            self.purchase_summaries[key] = summary

        return self.purchase_summaries

    # 집계 및 분석 메서드
    def get_monthly_summary(self, year_month: str) -> Dict[str, Decimal]:
        """특정 월의 매입 요약"""
        result = {
            'total_taxable': Decimal('0'),     # 과세 합계
            'total_tax_free': Decimal('0'),     # 면세 합계
            'total_amount': Decimal('0'),       # 전체 합계
            'supplier_count': 0                 # 협력사 수
        }

        suppliers = set()
        for purchase in self.purchases:
            if purchase.year_month == year_month:
                if purchase.tax_type == '과세':
                    result['total_taxable'] += purchase.final_amount
                else:
                    result['total_tax_free'] += purchase.final_amount
                result['total_amount'] += purchase.final_amount
                suppliers.add(purchase.supplier_code)

        result['supplier_count'] = len(suppliers)
        return result

    def get_supplier_summary(self, supplier_code: str) -> Dict[str, Any]:
        """특정 협력사의 매입 요약"""
        supplier_code = str(supplier_code)
        result = {
            'supplier': self.get_supplier(supplier_code),
            'monthly_data': {},
            'total_amount': Decimal('0')
        }

        for purchase in self.purchases:
            if purchase.supplier_code == supplier_code:
                if purchase.year_month not in result['monthly_data']:
                    result['monthly_data'][purchase.year_month] = {
                        'taxable': Decimal('0'),
                        'tax_free': Decimal('0'),
                        'total': Decimal('0')
                    }

                month_data = result['monthly_data'][purchase.year_month]
                if purchase.tax_type == '과세':
                    month_data['taxable'] += purchase.final_amount
                else:
                    month_data['tax_free'] += purchase.final_amount
                month_data['total'] += purchase.final_amount
                result['total_amount'] += purchase.final_amount

        return result

    def export_summary_to_df(self) -> pd.DataFrame:
        """요약 데이터를 DataFrame으로 변환"""
        if not self.purchase_summaries:
            self.create_purchase_summary()

        data = []
        for summary in self.purchase_summaries.values():
            data.append({
                '년월': summary.year_month,
                '협력사코드': summary.supplier_code,
                '협력사명': summary.supplier_name,
                '면과세구분명': summary.tax_type,
                '최종매입금액': float(summary.total_amount),
                'key': summary.key
            })

        df = pd.DataFrame(data)
        if not df.empty:
            df = df.sort_values(['협력사코드', '년월', '면과세구분명'])
        return df

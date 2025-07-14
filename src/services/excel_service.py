import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
import sys
import os

# kfunction 모듈 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from kfunction import read_excel_data

from ..models import Supplier, Purchase, Payment, TaxInvoice


class ExcelService:
    """Excel 파일 처리 서비스"""

    @staticmethod
    def read_excel_with_validation(file_path: str, sheet_name=0, header=0) -> pd.DataFrame:
        """Excel 파일 읽기 with 검증"""
        try:
            # kfunction의 read_excel_data 사용
            # sheet_name이 문자열인 경우 그대로 사용, 숫자인 경우 sheet 파라미터로 전달
            df = read_excel_data(file_path, sheet=sheet_name, header=header)
            return df
        except Exception as e:
            raise Exception(f"Excel 파일 읽기 오류: {str(e)}")

    @staticmethod
    def load_suppliers(file_path: str) -> List[Supplier]:
        """공급업체 데이터 로드"""
        df = ExcelService.read_excel_with_validation(file_path)

        suppliers = []
        for idx, row in df.iterrows():
            supplier = Supplier(
                id=str(row.get('사업자등록번호', idx)),
                business_number=str(row.get('사업자등록번호', '')),
                name=row.get('상호명', ''),
                representative=row.get('대표자', ''),
                address=row.get('주소', ''),
                business_type=row.get('업태', ''),
                business_category=row.get('종목', ''),
                phone=row.get('전화번호', ''),
                email=row.get('이메일', '')
            )
            suppliers.append(supplier)

        return suppliers

    @staticmethod
    def load_purchases(file_path: str) -> List[Purchase]:
        """구매 데이터 로드"""
        df = ExcelService.read_excel_with_validation(file_path)

        purchases = []
        for idx, row in df.iterrows():
            # 날짜 처리
            purchase_date = pd.to_datetime(row.get('거래일자', datetime.now()), errors='coerce')
            if pd.isna(purchase_date):
                purchase_date = datetime.now()

            purchase = Purchase(
                id=f"PUR_{idx}",
                supplier_id=str(row.get('사업자등록번호', '')),
                purchase_date=purchase_date,
                description=row.get('품목', ''),
                amount=float(row.get('금액', 0)),
                tax_amount=float(row.get('부가세', 0)),
                total_amount=float(row.get('합계', 0)),
                payment_status=row.get('지급상태', 'pending'),
                invoice_number=row.get('계산서번호', ''),
                department=row.get('부서', ''),
                project_code=row.get('프로젝트코드', '')
            )
            purchases.append(purchase)

        return purchases

    @staticmethod
    def load_payments(file_path: str) -> List[Payment]:
        """지급 데이터 로드"""
        df = ExcelService.read_excel_with_validation(file_path)

        payments = []
        for idx, row in df.iterrows():
            payment_date = pd.to_datetime(row.get('지급일자', datetime.now()), errors='coerce')
            if pd.isna(payment_date):
                payment_date = datetime.now()

            payment = Payment(
                id=f"PAY_{idx}",
                supplier_id=str(row.get('사업자등록번호', '')),
                payment_date=payment_date,
                amount=float(row.get('지급금액', 0)),
                payment_method=row.get('지급방법', '계좌이체'),
                bank_name=row.get('은행명', ''),
                account_number=row.get('계좌번호', ''),
                reference_number=row.get('참조번호', ''),
                description=row.get('적요', '')
            )
            payments.append(payment)

        return payments

    @staticmethod
    def load_tax_invoices(file_path: str, cached_df: pd.DataFrame = None) -> List[TaxInvoice]:
        """세금계산서 데이터 로드"""
        # 캐싱된 데이터가 있으면 사용
        if cached_df is not None:
            df = cached_df
        else:
            df = ExcelService.read_excel_with_validation(file_path)

        # MultiIndex 컬럼 처리 (매입대사2.ipynb 참고)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] if pd.isna(col[1]) else f"{col[0]}_{col[1]}" for col in df.columns]

        tax_invoices = []
        for idx, row in df.iterrows():
            issue_date = pd.to_datetime(row.get('발행일자', datetime.now()), errors='coerce')
            if pd.isna(issue_date):
                issue_date = datetime.now()

            tax_invoice = TaxInvoice(
                id=f"TAX_{idx}",
                invoice_number=str(row.get('국세청승인번호', f"TAX_{idx}")),
                supplier_id=str(row.get('공급자사업자번호', '')),
                issue_date=issue_date,
                supply_amount=float(row.get('공급가액', 0)),
                tax_amount=float(row.get('세액', 0)),
                total_amount=float(row.get('합계금액', 0)),
                invoice_type=row.get('계산서종류', '세금계산서'),
                description=row.get('품목', ''),
                buyer_business_number=str(row.get('공급받는자사업자번호', '')),
                electronic_invoice_status=row.get('전자세금계산서여부', 'Y')
            )
            tax_invoices.append(tax_invoice)

        return tax_invoices

    @staticmethod
    def export_to_excel(data: Dict, output_path: str):
        """데이터를 Excel로 내보내기"""
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            for sheet_name, df_data in data.items():
                if isinstance(df_data, pd.DataFrame):
                    df_data.to_excel(writer, sheet_name=sheet_name, index=False)
                elif isinstance(df_data, list):
                    df = pd.DataFrame(df_data)
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                elif isinstance(df_data, dict):
                    df = pd.DataFrame([df_data])
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

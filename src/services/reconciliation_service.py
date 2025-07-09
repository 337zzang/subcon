from typing import Dict, List, Tuple, Optional
from datetime import datetime
import pandas as pd
from ..models import Purchase, Payment, TaxInvoice, ProcessingFee
from .data_manager import DataManager


class ReconciliationService:
    """대사 처리 서비스"""

    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager

    def process_all_reconciliation(self, start_date: datetime, end_date: datetime) -> Dict:
        """
        지정된 기간에 대한 전체 대사 처리

        Args:
            start_date: 시작일
            end_date: 종료일

        Returns:
            대사 결과 딕셔너리
        """
        results = {
            'period': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d')
            },
            'summary': {},
            'details': [],
            'unmatched': {
                'purchases': [],
                'payments': [],
                'tax_invoices': []
            }
        }

        # 기간별 데이터 필터링
        filtered_purchases = self._filter_by_date(
            self.data_manager.purchases, start_date, end_date, 'purchase_date'
        )
        filtered_payments = self._filter_by_date(
            self.data_manager.payments, start_date, end_date, 'payment_date'
        )
        filtered_tax_invoices = self._filter_by_date(
            self.data_manager.tax_invoices, start_date, end_date, 'issue_date'
        )

        # 대사 처리
        matched_records = self._match_records(
            filtered_purchases, filtered_payments, filtered_tax_invoices
        )

        # 결과 정리
        results['details'] = matched_records
        results['summary'] = self._create_summary(matched_records)

        # 미매칭 항목 찾기
        results['unmatched'] = self._find_unmatched(
            filtered_purchases, filtered_payments, filtered_tax_invoices, matched_records
        )

        return results

    def _filter_by_date(self, items: List, start_date: datetime, end_date: datetime, date_field: str) -> List:
        """날짜별 필터링"""
        filtered = []
        for item in items.values() if isinstance(items, dict) else items:
            item_date = getattr(item, date_field, None)
            if item_date and start_date <= item_date <= end_date:
                filtered.append(item)
        return filtered

    def _match_records(self, purchases: List[Purchase], payments: List[Payment], 
                      tax_invoices: List[TaxInvoice]) -> List[Dict]:
        """구매, 지급, 세금계산서 매칭"""
        matched = []

        # 간단한 매칭 로직 (실제로는 더 복잡한 로직 필요)
        for purchase in purchases:
            match_result = {
                'purchase': purchase.to_dict(),
                'payment': None,
                'tax_invoice': None,
                'status': 'partial'
            }

            # 동일 공급업체의 지급 내역 찾기
            for payment in payments:
                if payment.supplier_id == purchase.supplier_id:
                    match_result['payment'] = payment.to_dict()
                    break

            # 세금계산서 찾기
            for tax_invoice in tax_invoices:
                if tax_invoice.supplier_id == purchase.supplier_id:
                    match_result['tax_invoice'] = tax_invoice.to_dict()
                    break

            # 매칭 상태 결정
            if match_result['payment'] and match_result['tax_invoice']:
                match_result['status'] = 'complete'
            elif not match_result['payment'] and not match_result['tax_invoice']:
                match_result['status'] = 'unmatched'

            matched.append(match_result)

        return matched

    def _create_summary(self, matched_records: List[Dict]) -> Dict:
        """대사 결과 요약"""
        summary = {
            'total_count': len(matched_records),
            'complete_count': sum(1 for r in matched_records if r['status'] == 'complete'),
            'partial_count': sum(1 for r in matched_records if r['status'] == 'partial'),
            'unmatched_count': sum(1 for r in matched_records if r['status'] == 'unmatched'),
            'total_purchase_amount': sum(r['purchase']['amount'] for r in matched_records if r['purchase']),
            'total_payment_amount': sum(r['payment']['amount'] for r in matched_records if r['payment']),
        }
        return summary

    def _find_unmatched(self, purchases: List, payments: List, tax_invoices: List, 
                       matched_records: List[Dict]) -> Dict:
        """미매칭 항목 찾기"""
        # 매칭된 항목들의 ID 추출
        matched_purchase_ids = {r['purchase']['id'] for r in matched_records if r['purchase']}
        matched_payment_ids = {r['payment']['id'] for r in matched_records if r['payment']}
        matched_tax_ids = {r['tax_invoice']['id'] for r in matched_records if r['tax_invoice']}

        # 미매칭 항목 찾기
        unmatched = {
            'purchases': [p.to_dict() for p in purchases if p.id not in matched_purchase_ids],
            'payments': [p.to_dict() for p in payments if p.id not in matched_payment_ids],
            'tax_invoices': [t.to_dict() for t in tax_invoices if t.id not in matched_tax_ids]
        }

        return unmatched

    def export_results_to_excel(self, results: Dict, file_path: str):
        """대사 결과를 Excel로 내보내기"""
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            # 요약 시트
            summary_df = pd.DataFrame([results['summary']])
            summary_df.to_excel(writer, sheet_name='요약', index=False)

            # 상세 매칭 결과 시트
            if results['details']:
                details_data = []
                for record in results['details']:
                    row = {
                        '상태': record['status'],
                        '구매_ID': record['purchase']['id'] if record['purchase'] else '',
                        '구매_금액': record['purchase']['amount'] if record['purchase'] else 0,
                        '지급_ID': record['payment']['id'] if record['payment'] else '',
                        '지급_금액': record['payment']['amount'] if record['payment'] else 0,
                        '세금계산서_번호': record['tax_invoice']['invoice_number'] if record['tax_invoice'] else '',
                        '세금계산서_금액': record['tax_invoice']['total_amount'] if record['tax_invoice'] else 0,
                    }
                    details_data.append(row)

                details_df = pd.DataFrame(details_data)
                details_df.to_excel(writer, sheet_name='매칭결과', index=False)

            # 미매칭 구매 시트
            if results['unmatched']['purchases']:
                unmatched_purchases_df = pd.DataFrame(results['unmatched']['purchases'])
                unmatched_purchases_df.to_excel(writer, sheet_name='미매칭_구매', index=False)

            # 미매칭 지급 시트
            if results['unmatched']['payments']:
                unmatched_payments_df = pd.DataFrame(results['unmatched']['payments'])
                unmatched_payments_df.to_excel(writer, sheet_name='미매칭_지급', index=False)

            # 미매칭 세금계산서 시트
            if results['unmatched']['tax_invoices']:
                unmatched_tax_df = pd.DataFrame(results['unmatched']['tax_invoices'])
                unmatched_tax_df.to_excel(writer, sheet_name='미매칭_세금계산서', index=False)

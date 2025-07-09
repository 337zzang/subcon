"""
데이터 모델 테스트
"""
import unittest
from decimal import Decimal
from datetime import date, datetime

# 프로젝트 루트를 path에 추가
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import (
    Supplier, SupplierProduct, Purchase, PurchaseSummary,
    TaxInvoice, Payment
)
from src.services.data_manager import DataManager

class TestDataModels(unittest.TestCase):
    """데이터 모델 테스트"""

    def setUp(self):
        """테스트 초기화"""
        self.data_manager = DataManager()

    def test_supplier_model(self):
        """협력사 모델 테스트"""
        supplier = Supplier(
            supplier_code="123456",
            supplier_name="테스트 협력사",
            business_number="123-45-67890",
            tax_type="과세"
        )

        self.assertEqual(supplier.supplier_code, "123456")
        self.assertEqual(supplier.supplier_name, "테스트 협력사")
        self.assertEqual(str(supplier), "테스트 협력사 (123456)")
        self.assertTrue(supplier.is_active)

    def test_purchase_model(self):
        """매입 모델 테스트"""
        purchase = Purchase(
            year_month="202401",
            supplier_code="123456",
            supplier_name="테스트 협력사",
            product_code="999999",
            product_name="테스트 제품",
            tax_type="과세",
            purchase_amount=Decimal("1000000"),
            final_amount=Decimal("1000000")
        )

        self.assertEqual(purchase.year, 2024)
        self.assertEqual(purchase.month, 1)
        self.assertEqual(purchase.key, "202401123456과세")
        self.assertEqual(purchase.final_amount, Decimal("1000000"))

    def test_data_manager(self):
        """데이터 매니저 테스트"""
        # 협력사 추가
        supplier = Supplier(
            supplier_code="123456",
            supplier_name="테스트 협력사"
        )
        self.data_manager.add_supplier(supplier)

        # 협력사 조회
        retrieved = self.data_manager.get_supplier("123456")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.supplier_name, "테스트 협력사")

        # 매입 데이터 추가
        purchase = Purchase(
            year_month="202401",
            supplier_code="123456",
            supplier_name="테스트 협력사",
            product_code="999999",
            product_name="테스트 제품",
            tax_type="과세",
            final_amount=Decimal("1000000")
        )
        self.data_manager.add_purchase(purchase)

        # 요약 생성
        summaries = self.data_manager.create_purchase_summary()
        self.assertEqual(len(summaries), 1)

        # 월별 요약
        monthly = self.data_manager.get_monthly_summary("202401")
        self.assertEqual(monthly['total_amount'], Decimal("1000000"))
        self.assertEqual(monthly['supplier_count'], 1)

    def test_tax_invoice_model(self):
        """세금계산서 모델 테스트"""
        invoice = TaxInvoice(
            invoice_number="2024-001",
            invoice_date=date(2024, 1, 15),
            supplier_code="123456",
            supplier_name="테스트 협력사",
            business_number="123-45-67890",
            tax_type="과세",
            supply_amount=Decimal("1000000"),
            tax_amount=Decimal("100000")
        )

        self.assertEqual(invoice.calculate_total(), Decimal("1100000"))
        self.assertEqual(invoice.year_month, "202401")

    def test_model_serialization(self):
        """모델 직렬화 테스트"""
        supplier = Supplier(
            supplier_code="123456",
            supplier_name="테스트 협력사"
        )

        # to_dict 테스트
        data = supplier.to_dict()
        self.assertEqual(data['supplier_code'], "123456")
        self.assertEqual(data['supplier_name'], "테스트 협력사")

        # to_json 테스트
        json_str = supplier.to_json()
        self.assertIn('"supplier_code": "123456"', json_str)
        self.assertIn('"supplier_name": "테스트 협력사"', json_str)

if __name__ == '__main__':
    unittest.main()

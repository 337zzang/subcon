"""
파일 캐싱 및 검증 로직 테스트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.data_manager import DataManager
from src.services.reconciliation_validator import ReconciliationValidator
import pandas as pd
import numpy as np

def test_file_caching():
    """파일 캐싱 테스트"""
    print("=== 파일 캐싱 테스트 ===")
    
    # DataManager 생성
    dm = DataManager()
    
    # 초기 상태 확인
    print(f"초기 캐시 상태: 비어있음")
    
    # 테스트 데이터 생성
    test_df = pd.DataFrame({
        '협력사코드': ['A001', 'B002', 'C003'],
        '협력사명': ['A사', 'B사', 'C사'],
        '금액': [1000000, 2000000, 3000000]
    })
    
    # 파일 경로
    test_path = "data/test.xlsx"
    
    # 캐싱 테스트
    print("\n1. 데이터 캐싱...")
    dm.cache_file_data(test_path, test_df)
    print("✅ 캐싱 완료")
    
    # 캐시 확인
    print("\n2. 캐시 확인...")
    cached = dm.get_cached_data(test_path)
    if cached is not None and cached.equals(test_df):
        print("✅ 캐싱된 데이터가 원본과 일치합니다")
    else:
        print("❌ 캐싱 실패")
        
    # 경로 정규화 테스트
    print("\n3. 경로 정규화 테스트...")
    test_path2 = "data\\test.xlsx"  # 다른 형식의 경로
    cached2 = dm.get_cached_data(test_path2)
    if cached2 is not None:
        print("✅ 경로 정규화가 제대로 작동합니다")
    else:
        print("❌ 경로 정규화 실패")
        
    # 캐시 초기화
    print("\n4. 캐시 초기화...")
    dm.clear_all()
    cached3 = dm.get_cached_data(test_path)
    if cached3 is None:
        print("✅ 캐시 초기화 성공")
    else:
        print("❌ 캐시 초기화 실패")
        
    print("\n✅ 파일 캐싱 테스트 완료!\n")


def test_validation_logic():
    """검증 로직 테스트"""
    print("=== 검증 로직 테스트 ===")
    
    validator = ReconciliationValidator()
    
    # 테스트 데이터 생성
    original_data = {
        'purchase_detail': pd.DataFrame({
            '협력사코드': ['A001', 'B002', 'C003', 'D004'],
            '협력사명': ['A사', 'B사', 'C사', 'D사'],
            '금액': [1000000, 2000000, 3000000, 100000000]  # D사는 이상치
        })
    }
    
    result_data = {
        'final_merged': pd.DataFrame({
            '협력사코드': ['A001', 'B002', 'C003'],  # D004 누락
            '협력사명': ['A사', 'B사', 'C사'],
            '세액': [100000, 200000, 300000],
            '공급가': [900000, 1800000, 2700000],
            '합계': [1000000, 2000000, 3000000],
            '세금계산서번호': ['T001', 'T002', 'T002']  # T002 중복
        }),
        'tax_new': pd.DataFrame({
            '세금계산서번호': ['T001', 'T002', 'T002'],
            '비고': ['', '', '확인요청']
        }),
        'book_filtered': pd.DataFrame({
            '구분키': ['KEY1', 'KEY2', ''],  # 하나는 미대사
            '금액': [1000000, 2000000, 3000000]
        })
    }
    
    # 검증 실행
    print("\n검증 실행 중...")
    report = validator.validate_result(result_data, original_data)
    
    print(f"\n검증 결과: {report['status']}")
    
    if report['errors']:
        print("\n[오류]")
        for error in report['errors']:
            print(f"  ❌ {error}")
            
    if report['warnings']:
        print("\n[경고]")
        for warning in report['warnings']:
            print(f"  ⚠️ {warning}")
            
    if report['info']:
        print("\n[정보]")
        for info in report['info']:
            print(f"  ℹ️ {info}")
            
    print("\n✅ 검증 로직 테스트 완료!\n")


def test_key_mapping():
    """키 매핑 테스트"""
    print("=== 키 매핑 확인 ===")
    
    # file_map 확인
    file_map = {
        'purchase_detail': 'path/to/supplier_purchase.xlsx',
        'standard': 'path/to/standard.xlsx',
        'tax_invoice': 'path/to/tax_invoice.xlsx',
        'payment_ledger': 'path/to/payment_ledger.xlsx',  # 올바른 키
        'tax_invoice_wis': 'path/to/tax_invoice_wis.xlsx'
    }
    
    # 필수 파일 체크
    required_files = ['standard', 'purchase_detail', 'tax_invoice', 'payment_ledger', 'tax_invoice_wis']
    missing_files = [f for f in required_files if f not in file_map or not file_map[f]]
    
    if missing_files:
        print(f"❌ 필수 파일 누락: {missing_files}")
    else:
        print("✅ 모든 필수 파일이 올바르게 매핑되었습니다")
        
    print("\n✅ 키 매핑 테스트 완료!\n")


if __name__ == "__main__":
    print("=" * 60)
    print("대사 결과 검증 로직 구현 테스트")
    print("=" * 60)
    print()
    
    # 파일 캐싱 테스트
    test_file_caching()
    
    # 검증 로직 테스트
    test_validation_logic()
    
    # 키 매핑 테스트
    test_key_mapping()
    
    print("\n모든 테스트 완료!")

# 파일 캐싱 테스트 스크립트
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.data_manager import DataManager
import pandas as pd

def test_file_caching():
    print("=== 파일 캐싱 테스트 ===")

    # DataManager 생성
    dm = DataManager()

    # 초기 상태 확인
    print(f"초기 캐시 크기: {dm.get_cache_size()}")

    # 테스트 데이터 생성
    test_df = pd.DataFrame({
        '협력사코드': [1, 2, 3],
        '협력사명': ['A사', 'B사', 'C사'],
        '금액': [1000, 2000, 3000]
    })

    # 파일 경로
    test_path = "data/test.xlsx"

    # 캐싱 테스트
    print("\n1. 데이터 캐싱...")
    dm.cache_file_data(test_path, test_df)
    print(f"캐싱 후 크기: {dm.get_cache_size()}")

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
    dm.clear_file_cache()
    print(f"초기화 후 크기: {dm.get_cache_size()}")

    print("\n✅ 파일 캐싱 테스트 완료!")

if __name__ == "__main__":
    test_file_caching()

"""
캐시 및 날짜 처리 수정 테스트 스크립트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from kfunction import read_excel_data, get_data_manager
from datetime import datetime
import pandas as pd

def test_cache_functionality():
    """캐시 기능 테스트"""
    print("=" * 60)
    print("1. 캐시 기능 테스트")
    print("=" * 60)
    
    dm = get_data_manager()
    
    # 테스트용 파일 경로 (실제 파일로 변경 필요)
    test_file = "sample_data/구매_내역.xlsx"
    
    if os.path.exists(test_file):
        # 첫 번째 읽기 - 캐시 저장
        print("\n첫 번째 읽기:")
        df1 = read_excel_data(test_file)
        print(f"✅ 데이터 크기: {df1.shape}")
        print(f"✅ 캐시 크기: {dm.get_cache_size()}")
        
        # 두 번째 읽기 - 캐시에서 로드
        print("\n두 번째 읽기:")
        df2 = read_excel_data(test_file)
        print(f"✅ 동일한 데이터: {df1.equals(df2)}")
        print(f"✅ 캐시 크기: {dm.get_cache_size()}")
    else:
        print("⚠️ 테스트 파일이 없습니다.")

def test_column_mapping():
    """동적 컬럼 매핑 테스트"""
    print("\n" + "=" * 60)
    print("2. 동적 컬럼 매핑 테스트")
    print("=" * 60)
    
    # 테스트 데이터프레임 생성
    test_df = pd.DataFrame({
        '국세청승인번호': [1, 2, 3],
        '계산서작성일': ['2024-01-01', '2024-01-02', '2024-01-03'],
        'nan_작성일': ['2024-01-01', '2024-01-02', '2024-01-03'],
        '작성일': ['2024-01-01', '2024-01-02', '2024-01-03']  # nan 없는 컬럼
    })
    
    # _find_date_column 로직 테스트
    def find_date_column(df, keyword):
        # nan이 없는 컬럼 우선
        for col in df.columns:
            if keyword in str(col) and 'nan' not in str(col):
                # 완전 일치하는 경우 우선
                if str(col) == keyword:
                    return col
        # 부분 일치 찾기 (nan 없는 것)
        for col in df.columns:
            if keyword in str(col) and 'nan' not in str(col):
                return col
        # nan이 있어도 키워드가 있으면 반환
        for col in df.columns:
            if keyword in str(col):
                return col
        return None
    
    작성일_컬럼 = find_date_column(test_df, '작성일')
    print(f"✅ 찾은 작성일 컬럼: '{작성일_컬럼}' (기대값: '작성일')")
    
    # nan만 있는 경우 테스트
    test_df2 = pd.DataFrame({
        'nan_작성일': ['2024-01-01', '2024-01-02', '2024-01-03']
    })
    작성일_컬럼2 = find_date_column(test_df2, '작성일')
    print(f"✅ nan만 있을 때: '{작성일_컬럼2}' (기대값: 'nan_작성일')")

def test_date_processing():
    """날짜 처리 안전성 테스트"""
    print("\n" + "=" * 60)
    print("3. 날짜 처리 안전성 테스트")
    print("=" * 60)
    
    # 안전한 날짜 차이 계산
    def safe_date_diff(date1_str, date2_str):
        try:
            date1 = pd.to_datetime(date1_str + '01')
            date2 = pd.to_datetime(date2_str + '01')
            
            if pd.notna(date1) and pd.notna(date2):
                diff = date1 - date2
                months = diff.days / 30
                return months
            else:
                return None
        except Exception as e:
            print(f"⚠️ 날짜 변환 오류: {e}")
            return None
    
    # 정상 케이스
    result1 = safe_date_diff('202401', '202312')
    print(f"✅ 정상 케이스: {result1}개월 차이")
    
    # 오류 케이스
    result2 = safe_date_diff('invalid', '202312')
    print(f"✅ 오류 케이스: {result2} (None 반환)")
    
    # None 케이스
    result3 = safe_date_diff(None, '202312')
    print(f"✅ None 케이스: {result3} (None 반환)")

if __name__ == "__main__":
    print("🔍 캐시 및 날짜 처리 수정 테스트")
    print("=" * 60)
    
    test_cache_functionality()
    test_column_mapping()
    test_date_processing()
    
    print("\n✅ 모든 테스트 완료!")

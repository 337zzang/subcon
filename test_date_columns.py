# 매입세금계산서 파일의 실제 컬럼 확인
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kfunction import read_excel_data

# 매입세금계산서 파일 읽기
file_path = "data/매입세금계산서.xlsx"
if os.path.exists(file_path):
    df = read_excel_data(file_path)

    print("=== 매입세금계산서 컬럼 정보 ===")
    print(f"컬럼 타입: {type(df.columns)}")

    if isinstance(df.columns, pd.MultiIndex):
        print("\nMultiIndex 컬럼 발견!")
        print("첫 10개 컬럼:")
        for i, col in enumerate(df.columns[:10]):
            print(f"  {i}: {col}")

        # 평탄화 테스트
        flattened = [col[0] if isinstance(col, tuple) else col for col in df.columns]
        print("\n평탄화된 컬럼:")
        print([col for col in flattened if '작성일' in str(col) or '발급일' in str(col)])
    else:
        print("\n일반 컬럼:")
        date_cols = [col for col in df.columns if '작성일' in str(col) or '발급일' in str(col)]
        print(f"날짜 관련 컬럼: {date_cols}")

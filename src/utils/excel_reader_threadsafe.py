import pandas as pd
import os
from pathlib import Path

def read_excel_data_threadsafe(
    file_path: str,
    sheet: int | str = 0,
    header: int | list[int] = 0,
) -> pd.DataFrame:
    """
    Excel 파일을 DataFrame으로 읽어오는 스레드 안전 함수
    백그라운드 스레드에서도 안전하게 사용 가능 (pandas 사용)
    """
    print(f"[INFO] Thread-safe: '{file_path}' 읽는 중…")
    
    try:
        # pandas의 read_excel 사용 (COM 객체 미사용)
        df = pd.read_excel(
            file_path,
            sheet_name=sheet if isinstance(sheet, str) else sheet,
            header=header,
            engine='openpyxl'  # openpyxl 엔진 사용 (COM 객체 미사용)
        )
        
        # 빈 행/열 제거
        df = df.dropna(how='all')  # 모든 값이 NaN인 행 제거
        df = df.dropna(axis=1, how='all')  # 모든 값이 NaN인 열 제거
        
        print(f"[INFO] 읽기 완료: {len(df)} 행")
        return df
        
    except Exception as e:
        print(f"[ERROR] Excel 읽기 실패: {str(e)}")
        raise

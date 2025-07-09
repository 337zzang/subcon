"""
Excel 데이터 처리 서비스
기존 kfunction.py의 기능과 매입대사 프로세스를 통합
"""
import pandas as pd
import numpy as np
import win32com.client as win32
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import gc

class ExcelService:
    def __init__(self):
        self.data_cache: Dict[str, pd.DataFrame] = {}

    def read_excel_data(self, 
                       file_path: str,
                       sheet: int | str = 0,
                       header: int | list[int] = 0) -> pd.DataFrame:
        """
        Excel 파일을 DataFrame으로 읽어오는 함수 (pywin32 사용)
        기존 kfunction.py의 read_excel_data 함수 활용
        """
        print(f"[INFO] '{file_path}' 읽는 중…")
        excel, wb = None, None
        try:
            excel = win32.Dispatch("Excel.Application")
            excel.Visible = False
            excel.DisplayAlerts = False

            wb = excel.Workbooks.Open(str(Path(file_path).resolve()))

            # 시트 처리
            if isinstance(sheet, int):
                ws = wb.Worksheets(sheet + 1)  # 1-based index
            else:
                ws = wb.Worksheets(sheet)

            # 데이터 범위 가져오기
            used_range = ws.UsedRange
            data = used_range.Value

            # DataFrame 생성
            if data:
                df = pd.DataFrame(list(data))
                if header is not None:
                    if isinstance(header, int):
                        df.columns = df.iloc[header]
                        df = df.iloc[header + 1:].reset_index(drop=True)
                    else:
                        # 다중 헤더 처리
                        headers = [df.iloc[h] for h in header]
                        df.columns = pd.MultiIndex.from_arrays(headers)
                        df = df.iloc[max(header) + 1:].reset_index(drop=True)
                return df
            else:
                return pd.DataFrame()

        except Exception as e:
            print(f"[ERROR] Excel 읽기 실패: {e}")
            raise
        finally:
            if wb:
                wb.Close(False)
            if excel:
                excel.Quit()
            gc.collect()

    def process_supplier_purchase_data(self, config: dict) -> pd.DataFrame:
        """
        협력사 매입 데이터 처리 (매입대사2.ipynb의 로직)
        """
        # 1. 기준 데이터 읽기
        df_standard = self.read_excel_data(
            f"data/{config['excel_files']['standard']}", 
            sheet=0
        )

        # 2. 협력사단품별매입 데이터 읽기
        df_purchase = self.read_excel_data(
            f"data/{config['excel_files']['supplier_purchase']}", 
            header=0
        )

        # Grand Total 행 제거
        df_purchase = df_purchase.drop(0).reset_index(drop=True)

        # 3. 필요한 컬럼 선택 및 피벗
        df_pivot = df_purchase.pivot_table(
            index=["년월", "협력사코드", "협력사명", "단품코드", "단품명", "면과세구분명"],
            values="최종매입금액",
            aggfunc="sum"
        ).reset_index()

        # 4. 데이터 타입 변환
        df_pivot['협력사코드'] = df_pivot['협력사코드'].astype(int).astype(str)
        df_pivot['단품코드'] = df_pivot['단품코드'].astype(int).astype(str)

        df_standard_subset = df_standard[['협력사코드', '단품코드']].drop_duplicates()
        df_standard_subset['협력사코드'] = df_standard_subset['협력사코드'].astype(int).astype(str)
        df_standard_subset['단품코드'] = df_standard_subset['단품코드'].astype(int).astype(str)

        # 5. Inner join
        df_final = pd.merge(
            df_pivot, 
            df_standard_subset, 
            on=['협력사코드', '단품코드'], 
            how='inner'
        )

        # 6. 협력사별 집계
        df_final_pivot = df_final.groupby(["년월", "협력사코드", "면과세구분명"]).agg({
            "협력사명": "first",
            "최종매입금액": "sum"
        }).reset_index()

        # 7. 정렬 및 키 생성
        df_final_pivot = df_final_pivot.sort_values(by=["협력사코드", "년월", "면과세구분명"])
        df_final_pivot["key"] = (
            df_final_pivot["년월"].astype(int).astype(str) + 
            df_final_pivot["협력사코드"].astype(str) + 
            df_final_pivot["면과세구분명"]
        )

        # 8. 0원 제거
        df_final_pivot = df_final_pivot[df_final_pivot.최종매입금액 != 0]

        return df_final_pivot

    def save_to_excel(self, df: pd.DataFrame, output_path: str):
        """DataFrame을 Excel로 저장"""
        df.to_excel(output_path, index=False)
        print(f"[INFO] 파일 저장 완료: {output_path}")

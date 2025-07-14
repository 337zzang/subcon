import win32com.client as win32
import pandas as pd, os, gc
import sys

# DataManager 싱글톤 인스턴스
_data_manager = None

def get_data_manager():
    """DataManager 싱글톤 인스턴스 반환"""
    global _data_manager
    if _data_manager is None:
        # src 경로를 sys.path에 추가
        src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        
        from services.data_manager import DataManager
        _data_manager = DataManager()
    return _data_manager

def read_excel_data(
    file_path: str,
    sheet: int | str = 0,      # 인덱스(0‑기준) 또는 시트명
    header: int | list[int] = 0,
) -> pd.DataFrame:
    """
    Excel 파일을 DataFrame으로 읽어 오는 함수 (pywin32 사용, 시트 자동 검증)
    - sheet: 0‑기준 인덱스(int) 또는 정확한 시트명(str)
    - header: pandas.read_excel과 동일하게 단일/다중 헤더 지원
    """
    # 캐시 확인
    dm = get_data_manager()
    cached_data = dm.get_cached_data(file_path)
    if cached_data is not None:
        print(f"[INFO] '{file_path}' 캐시에서 로드")
        return cached_data.copy()
    
    print(f"[INFO] '{file_path}' 읽는 중…")
    excel, wb = None, None
    try:
        excel = win32.Dispatch("Excel.Application")
        excel.Visible = excel.DisplayAlerts = False
        wb = excel.Workbooks.Open(os.path.abspath(file_path))

        # -------- 시트 선택 로직 -------- #
        if isinstance(sheet, str):
            try:
                ws = wb.Worksheets(sheet)
            except Exception:
                existing = [wb.Worksheets(i).Name for i in range(1, wb.Sheets.Count+1)]
                raise ValueError(f"'{sheet}' 시트를 찾을 수 없습니다. 존재 시트: {existing}")
        else:                             # int 인덱스
            max_idx = wb.Sheets.Count - 1   # 0‑기준 최대 인덱스
            if not (0 <= sheet <= max_idx):
                raise IndexError(f"시트 인덱스 {sheet} 범위 초과(0~{max_idx}).")
            ws = wb.Worksheets(sheet + 1)   # COM은 1‑기준

        # -------- 데이터 추출 -------- #
        used_range = ws.UsedRange
        data = list(used_range.Value)           # 2‑D tuple → list 변환
        data = [[cell if cell is not None else None for cell in row] for row in data]

        # -------- DataFrame 구성 -------- #
        if isinstance(header, list):
            columns = pd.MultiIndex.from_arrays([data[h] for h in header])
            df = pd.DataFrame(data[max(header)+1:], columns=columns)
        else:
            if header >= 0:
                df = pd.DataFrame(data[header+1:], columns=data[header])
            else:
                df = pd.DataFrame(data)

        # -------- 숫자/날짜 자동 형 변환 -------- #
        # 안전한 숫자 변환: 각 컬럼을 개별적으로 처리
        for col in df.columns:
            try:
                # Series인지 확인하고 처리
                column_data = df[col]
                if hasattr(column_data, 'dtype') and column_data.dtype == 'object':
                    # errors='coerce'로 변경 (변환 불가능한 값은 NaN으로)
                    numeric_series = pd.to_numeric(column_data, errors='coerce')
                    # NaN이 아닌 값이 있으면 변환 적용
                    if numeric_series.notna().any():
                        df[col] = numeric_series.where(numeric_series.notna(), column_data)
            except (TypeError, ValueError, AttributeError) as e:
                # 변환할 수 없는 컬럼은 원본 유지
                continue
        
        # 캐시에 저장
        dm.cache_file_data(file_path, df)
        print(f"[INFO] '{file_path}' 캐시에 저장")
        
        return df

    finally:
        if wb: wb.Close(False)
        if excel: excel.Quit()
        del wb, excel
        gc.collect()

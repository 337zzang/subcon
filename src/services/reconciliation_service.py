"""
매입대사 서비스
노트북의 전체 대사 로직을 구현
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Tuple, Optional
from datetime import datetime
from decimal import Decimal
import gc

from .excel_service import ExcelService
from .data_manager import DataManager

class ReconciliationService:
    """매입대사 서비스"""

    def __init__(self, excel_service: ExcelService):
        self.excel_service = excel_service
        self.data_manager = excel_service.get_data_manager()
        self.reconciliation_results = {}

    def process_all_reconciliation(self, config: dict) -> Dict[str, pd.DataFrame]:
        """전체 대사 프로세스 실행"""
        results = {}

        try:
            # 1. 협력사단품별매입 처리 (이미 excel_service에 구현됨)
            print("[1/6] 협력사단품별매입 데이터 처리 중...")
            df_final_pivot = self.excel_service.process_supplier_purchase_data(config)
            results['supplier_purchase_summary'] = df_final_pivot.copy()

            # 2. 세금계산서(WIS) 처리
            print("[2/6] 매입세금계산서(WIS) 데이터 처리 중...")
            df_tax_wis = self._process_tax_invoice_wis(config)
            results['tax_invoice_wis'] = df_tax_wis

            # 3. 세금계산서 처리
            print("[3/6] 매입세금계산서 데이터 처리 중...")
            df_tax_hifi = self._process_tax_invoice_hifi(config)

            # 4. 세금계산서 데이터 병합
            print("[4/6] 세금계산서 데이터 병합 중...")
            df_tax_new = self._merge_tax_data(df_tax_wis, df_tax_hifi, df_final_pivot)
            results['tax_invoice_merged'] = df_tax_new

            # 5. 대사 실행
            print("[5/6] 매입-세금계산서 대사 실행 중...")
            df_final_result, df_tax_result = self._execute_reconciliation(
                df_final_pivot, df_tax_new
            )
            results['reconciliation_result'] = df_final_result
            results['tax_matched'] = df_tax_result

            # 6. 대사 요약 생성
            print("[6/6] 대사 요약 생성 중...")
            summary = self._create_reconciliation_summary(df_final_result, df_tax_result)
            results['summary'] = summary

            self.reconciliation_results = results
            return results

        except Exception as e:
            print(f"[ERROR] 대사 처리 중 오류: {e}")
            raise

    def _process_tax_invoice_wis(self, config: dict) -> pd.DataFrame:
        """매입세금계산서(WIS) 처리"""
        file_path = f"data/{config['excel_files']['tax_invoice_wis']}"

        # 데이터 읽기
        df = self.excel_service.read_excel_data(file_path)

        # 필요한 컬럼만 선택
        df_tax = df[["협력사코드", "계산서작성일", "협력사명", "계산서구분", 
                     "사업자번호", "공급가액", "세액", "국세청승인번호"]]

        # 협력사코드를 문자열로 변환
        df_tax['협력사코드'] = df_tax['협력사코드'].astype(str)

        return df_tax

    def _process_tax_invoice_hifi(self, config: dict) -> pd.DataFrame:
        """매입세금계산서 처리 (HIFI)"""
        file_path = f"data/{config['excel_files']['tax_invoice']}"

        # MultiIndex 헤더로 읽기
        df = self.excel_service.read_excel_data(file_path, sheet=0, header=[0,1])

        # MultiIndex 컬럼 평탄화
        df.columns = [col[0] if pd.isna(col[1]) else f"{col[0]}_{col[1]}" 
                      for col in df.columns]

        # 컬럼 매핑
        column_mapping = {
            '국세청승인번호': '국세청승인번호',
            '업체사업자번호': '업체사업자번호',
            '국세청작성일': 'nan_작성일',
            '국세청발급일': 'nan_발급일'
        }

        # lookup_df 생성
        lookup_df = df[[column_mapping['국세청승인번호'],
                       column_mapping['업체사업자번호'],
                       column_mapping['국세청작성일'],
                       column_mapping['국세청발급일']]].drop_duplicates(
                           subset=column_mapping['국세청승인번호'], keep='first')

        # 컬럼명 변경
        lookup_df = lookup_df.rename(columns={
            column_mapping['국세청승인번호']: '국세청승인번호',
            column_mapping['업체사업자번호']: '업체사업자번호',
            column_mapping['국세청작성일']: '국세청작성일',
            column_mapping['국세청발급일']: '국세청발급일'
        })

        return lookup_df

    def _merge_tax_data(self, df_tax_wis: pd.DataFrame, 
                       df_tax_hifi: pd.DataFrame,
                       df_final_pivot: pd.DataFrame) -> pd.DataFrame:
        """세금계산서 데이터 병합"""
        # 협력사코드 목록으로 필터링
        df_tax_sort = df_tax_wis[df_tax_wis.협력사코드.isin(
            df_final_pivot.협력사코드.tolist()
        )]

        # HIFI 데이터와 병합
        df_tax_new = pd.merge(df_tax_sort, df_tax_hifi, 
                             on='국세청승인번호', how='left')

        # 날짜 변환
        df_tax_new['국세청작성일'] = pd.to_datetime(
            df_tax_new['국세청작성일'], errors='coerce'
        )
        df_tax_new['국세청발급일'] = pd.to_datetime(
            df_tax_new['국세청발급일'], errors='coerce'
        )

        # timezone 제거
        if pd.api.types.is_datetime64tz_dtype(df_tax_new['국세청작성일']):
            df_tax_new['국세청작성일'] = df_tax_new['국세청작성일'].dt.tz_convert(None)
        if pd.api.types.is_datetime64tz_dtype(df_tax_new['국세청발급일']):
            df_tax_new['국세청발급일'] = df_tax_new['국세청발급일'].dt.tz_convert(None)

        # 업체사업자번호 정리
        df_tax_new["업체사업자번호"] = df_tax_new["업체사업자번호"].astype(str).str.replace("-", "", regex=True)

        # 작성년도와 작성월 추출
        df_tax_new['작성년도'] = df_tax_new['국세청작성일'].dt.year
        df_tax_new['작성월'] = df_tax_new['국세청작성일'].dt.month

        # 금액 변환
        df_tax_new["공급가액"] = pd.to_numeric(df_tax_new["공급가액"], errors="coerce")
        df_tax_new["세액"] = pd.to_numeric(df_tax_new["세액"], errors="coerce")

        # 대사 상태 컬럼 추가
        df_tax_new['대사여부'] = ""
        df_tax_new['구분키'] = ""

        return df_tax_new

    def _execute_reconciliation(self, df_final_pivot: pd.DataFrame,
                               df_tax_new: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """대사 로직 실행"""
        # 데이터 복사
        df_final = df_final_pivot.copy()
        df_tax = df_tax_new.copy()

        # df_final에 년/월 컬럼 추가
        df_final['년'] = df_final['년월'].astype(str).str[:4].astype(int)
        df_final['월'] = df_final['년월'].astype(str).str[4:6].astype(int)

        # 대사 결과 컬럼 추가
        df_final['국세청작성일'] = None
        df_final['국세청발급일'] = None
        df_final['국세청공급가액'] = None
        df_final['국세청세액'] = None
        df_final['구분키'] = ""
        df_final['국세청승인번호'] = None
        df_final['업체사업자번호'] = None

        # 허용 오차
        tolerance = 1e-6

        # Step A: 금액대사 (1:1 대사)
        self._execute_amount_matching(df_final, df_tax, tolerance)

        # Step A-2: 금액대사(수기확인)
        self._execute_amount_matching_manual(df_final, df_tax, tolerance)

        # Step B: 순차대사 (1:N 대사)
        self._execute_sequential_matching(df_final, df_tax, tolerance)

        # Step B-2: 순차대사(수기확인)
        self._execute_sequential_matching_manual(df_final, df_tax, tolerance)

        # Step C: 부분대사
        self._execute_partial_matching(df_final, df_tax, tolerance)

        # Step D: 미대사(수기확인)
        self._execute_manual_check(df_final, df_tax)

        return df_final, df_tax

    def _execute_amount_matching(self, df_final: pd.DataFrame, 
                                df_tax: pd.DataFrame, tolerance: float):
        """금액대사 (1:1) 실행"""
        for idx, row in df_final.iterrows():
            협력사코드_final = row['협력사코드']
            년도_final = row['년']
            월_final = row['월']
            금액_final = row['최종매입금액']

            # 면과세구분에 따른 계산서구분 설정
            if row['면과세구분명'] in ["과세", "영세"]:
                invoice_condition = "일반세금계산서"
            else:
                invoice_condition = "일반계산서"

            condition = (
                (df_tax['협력사코드'] == 협력사코드_final) &
                (df_tax['작성년도'] == 년도_final) &
                (df_tax['작성월'] == 월_final) &
                (df_tax['공급가액'] == 금액_final) &
                (df_tax['대사여부'] == "") &
                (df_tax['계산서구분'] == invoice_condition)
            )
            df_candidates = df_tax.loc[condition]

            if not df_candidates.empty:
                first_index = df_candidates.index[0]
                self._update_matching_result(df_final, df_tax, idx, first_index, 
                                           row['key'], "금액대사", 1)

    def _execute_amount_matching_manual(self, df_final: pd.DataFrame,
                                       df_tax: pd.DataFrame, tolerance: float):
        """금액대사(수기확인) 실행"""
        for idx, row in df_final.iterrows():
            # 이미 매핑된 경우 건너뛰기
            if pd.notnull(row['국세청작성일']):
                continue

            협력사코드_final = row['협력사코드']
            년도_final = row['년']
            월_final = row['월']
            금액_final = row['최종매입금액']

            # 계산서구분 조건 제외
            condition = (
                (df_tax['협력사코드'] == 협력사코드_final) &
                (df_tax['작성년도'] == 년도_final) &
                (df_tax['작성월'] == 월_final) &
                (df_tax['공급가액'] == 금액_final) &
                (df_tax['대사여부'] == "")
            )
            df_candidates = df_tax.loc[condition]

            if not df_candidates.empty:
                first_index = df_candidates.index[0]
                self._update_matching_result(df_final, df_tax, idx, first_index,
                                           row['key'], "금액대사(수기확인)", 1)

    def _execute_sequential_matching(self, df_final: pd.DataFrame,
                                    df_tax: pd.DataFrame, tolerance: float):
        """순차대사 (1:N) 실행"""
        for idx, row in df_final.iterrows():
            if pd.notnull(row['국세청작성일']):
                continue

            협력사코드_final = row['협력사코드']
            년도_final = row['년']
            월_final = row['월']
            target_amount = row['최종매입금액']

            if row['면과세구분명'] in ["과세", "영세"]:
                invoice_condition = "일반세금계산서"
            else:
                invoice_condition = "일반계산서"

            candidates = df_tax[
                (df_tax['협력사코드'] == 협력사코드_final) &
                (df_tax['작성년도'] == 년도_final) &
                (df_tax['작성월'] == 월_final) &
                (df_tax['대사여부'] == "") &
                (df_tax['계산서구분'] == invoice_condition)
            ]

            if candidates.empty:
                continue

            # FIFO 방식으로 정렬
            candidates = candidates.sort_values(by='국세청작성일')
            cumulative_sum = 0.0
            selected_indices = []

            for cand_idx, cand_row in candidates.iterrows():
                cumulative_sum += cand_row['공급가액']
                selected_indices.append(cand_idx)

                if np.abs(cumulative_sum - target_amount) < tolerance:
                    self._update_sequential_matching_result(
                        df_final, df_tax, idx, selected_indices,
                        candidates, row['key'], "순차대사"
                    )
                    break

    def _execute_sequential_matching_manual(self, df_final: pd.DataFrame,
                                          df_tax: pd.DataFrame, tolerance: float):
        """순차대사(수기확인) 실행"""
        # 순차대사와 동일하지만 계산서구분 조건 제외
        for idx, row in df_final.iterrows():
            if pd.notnull(row['국세청작성일']):
                continue

            협력사코드_final = row['협력사코드']
            년도_final = row['년']
            월_final = row['월']
            target_amount = row['최종매입금액']

            candidates = df_tax[
                (df_tax['협력사코드'] == 협력사코드_final) &
                (df_tax['작성년도'] == 년도_final) &
                (df_tax['작성월'] == 월_final) &
                (df_tax['대사여부'] == "")
            ]

            if candidates.empty:
                continue

            candidates = candidates.sort_values(by='국세청작성일')
            cumulative_sum = 0.0
            selected_indices = []

            for cand_idx, cand_row in candidates.iterrows():
                cumulative_sum += cand_row['공급가액']
                selected_indices.append(cand_idx)

                if np.abs(cumulative_sum - target_amount) < tolerance:
                    self._update_sequential_matching_result(
                        df_final, df_tax, idx, selected_indices,
                        candidates, row['key'], "순차대사(수기확인)"
                    )
                    break

    def _execute_partial_matching(self, df_final: pd.DataFrame,
                                 df_tax: pd.DataFrame, tolerance: float):
        """부분대사 실행"""
        for idx, row in df_final.iterrows():
            if pd.notnull(row['국세청작성일']):
                continue

            협력사코드_final = row['협력사코드']
            년도_final = row['년']
            월_final = row['월']

            # 같은 월의 모든 세금계산서 합계
            candidates = df_tax[
                (df_tax['협력사코드'] == 협력사코드_final) &
                (df_tax['작성년도'] == 년도_final) &
                (df_tax['작성월'] == 월_final)
            ]

            if not candidates.empty:
                # 가장 빠른 작성일과 발급일
                mapped_date = candidates['국세청작성일'].min()
                mapped_issue_date = candidates['국세청발급일'].min()
                mapped_supply = candidates['공급가액'].sum()
                mapped_tax = candidates['세액'].sum()

                df_final.at[idx, '국세청작성일'] = mapped_date
                df_final.at[idx, '국세청발급일'] = mapped_issue_date
                df_final.at[idx, '국세청공급가액'] = mapped_supply
                df_final.at[idx, '국세청세액'] = mapped_tax
                df_final.at[idx, '구분키'] = "부분대사"

                # 첫 번째 후보의 정보 사용
                if len(candidates) > 0:
                    first_idx = candidates.index[0]
                    df_final.at[idx, '국세청승인번호'] = candidates.loc[first_idx, '국세청승인번호']
                    df_final.at[idx, '업체사업자번호'] = candidates.loc[first_idx, '업체사업자번호']

    def _execute_manual_check(self, df_final: pd.DataFrame, df_tax: pd.DataFrame):
        """미대사(수기확인) 처리"""
        # 남은 세금계산서 중 금액이 0이 아닌 것들
        unmatched_tax = df_tax[
            (df_tax['대사여부'] == "") & 
            (df_tax['공급가액'] != 0)
        ]

        for idx, row in unmatched_tax.iterrows():
            df_tax.at[idx, '대사여부'] = f"{row['협력사코드']}{row['작성년도']}{row['작성월']:02d}-미대사"
            df_tax.at[idx, '구분키'] = "수기확인"

    def _update_matching_result(self, df_final: pd.DataFrame, df_tax: pd.DataFrame,
                               final_idx: int, tax_idx: int, key: str,
                               matching_type: str, seq_num: int):
        """대사 결과 업데이트"""
        # df_final 업데이트
        df_final.at[final_idx, '국세청작성일'] = df_tax.at[tax_idx, '국세청작성일']
        df_final.at[final_idx, '국세청발급일'] = df_tax.at[tax_idx, '국세청발급일']
        df_final.at[final_idx, '국세청공급가액'] = df_tax.at[tax_idx, '공급가액']
        df_final.at[final_idx, '국세청세액'] = df_tax.at[tax_idx, '세액']
        df_final.at[final_idx, '구분키'] = matching_type
        df_final.at[final_idx, '국세청승인번호'] = df_tax.at[tax_idx, '국세청승인번호']
        df_final.at[final_idx, '업체사업자번호'] = df_tax.at[tax_idx, '업체사업자번호']

        # df_tax 업데이트
        df_tax.at[tax_idx, '대사여부'] = f"{key}-{seq_num}"
        df_tax.at[tax_idx, '구분키'] = matching_type

    def _update_sequential_matching_result(self, df_final: pd.DataFrame,
                                         df_tax: pd.DataFrame, final_idx: int,
                                         selected_indices: list, candidates: pd.DataFrame,
                                         key: str, matching_type: str):
        """순차대사 결과 업데이트"""
        mapped_date = candidates.loc[selected_indices, '국세청작성일'].min()
        mapped_issue_date = candidates.loc[selected_indices, '국세청발급일'].min()
        mapped_supply = candidates.loc[selected_indices, '공급가액'].sum()
        mapped_tax = candidates.loc[selected_indices, '세액'].sum()

        df_final.at[final_idx, '국세청작성일'] = mapped_date
        df_final.at[final_idx, '국세청발급일'] = mapped_issue_date
        df_final.at[final_idx, '국세청공급가액'] = mapped_supply
        df_final.at[final_idx, '국세청세액'] = mapped_tax
        df_final.at[final_idx, '구분키'] = matching_type

        # 첫 번째 후보의 정보 사용
        first_candidate_index = selected_indices[0]
        df_final.at[final_idx, '국세청승인번호'] = candidates.loc[first_candidate_index, '국세청승인번호']
        df_final.at[final_idx, '업체사업자번호'] = candidates.loc[first_candidate_index, '업체사업자번호']

        # 각 후보에 순번 부여
        for i, si in enumerate(selected_indices, start=1):
            df_tax.at[si, '대사여부'] = f"{key}-{i}"
            df_tax.at[si, '구분키'] = matching_type

    def _create_reconciliation_summary(self, df_final: pd.DataFrame,
                                     df_tax: pd.DataFrame) -> pd.DataFrame:
        """대사 요약 생성"""
        summary_data = []

        # 전체 요약
        total_purchase = df_final['최종매입금액'].sum()
        total_tax_matched = df_final['국세청공급가액'].sum()

        summary_data.append({
            '구분': '전체',
            '매입금액': total_purchase,
            '세금계산서금액': total_tax_matched,
            '차이': total_purchase - total_tax_matched,
            '대사율': (total_tax_matched / total_purchase * 100) if total_purchase > 0 else 0
        })

        # 구분키별 요약
        for key_type in df_final['구분키'].unique():
            if key_type and key_type != "":
                key_data = df_final[df_final['구분키'] == key_type]
                summary_data.append({
                    '구분': key_type,
                    '매입금액': key_data['최종매입금액'].sum(),
                    '세금계산서금액': key_data['국세청공급가액'].sum(),
                    '차이': 0,
                    '대사율': 100
                })

        return pd.DataFrame(summary_data)

    def save_results(self, output_path: str = "OUT"):
        """대사 결과를 엑셀로 저장"""
        output_dir = Path(output_path)
        output_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 메인 결과 파일
        main_file = output_dir / f"매입대사결과_{timestamp}.xlsx"

        with pd.ExcelWriter(main_file, engine='openpyxl') as writer:
            # 각 시트에 결과 저장
            for sheet_name, df in self.reconciliation_results.items():
                if isinstance(df, pd.DataFrame) and not df.empty:
                    # 시트 이름 정리 (최대 31자)
                    clean_name = sheet_name.replace('_', ' ').title()[:31]
                    df.to_excel(writer, sheet_name=clean_name, index=False)

        print(f"✅ 대사 결과 저장 완료: {main_file}")

        # 미대사 항목만 별도 저장
        if 'reconciliation_result' in self.reconciliation_results:
            df_result = self.reconciliation_results['reconciliation_result']
            unmatched = df_result[df_result['구분키'].isin(['', '부분대사', '수기확인'])]

            if not unmatched.empty:
                unmatched_file = output_dir / f"미대사항목_{timestamp}.xlsx"
                unmatched.to_excel(unmatched_file, index=False)
                print(f"✅ 미대사 항목 저장 완료: {unmatched_file}")

        return str(main_file)

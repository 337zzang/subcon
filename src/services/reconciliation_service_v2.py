"""
매입대사 서비스 v2 - 매입대사2.ipynb 로직 이식
"""
import pandas as pd
import numpy as np
import win32com.client as win32
import os
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from pathlib import Path

# kfunction 모듈 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from kfunction import read_excel_data

from ..models.reconciliation_models import DataContainer


class ReconciliationService:
    """매입대사2.ipynb의 로직을 그대로 이식한 서비스"""
    
    def __init__(self):
        self.data_container = DataContainer()
        
        # 노트북에서 사용하는 DataFrame들
        self.df = None  # 협력사단품별매입
        self.df_standard = None  # 기준
        self.df_tax_hifi = None  # 매입세금계산서
        self.df_book = None  # 지불보조장
        self.df_num = None  # 매입세금계산서(WIS)
        self.df_processing = None  # 임가공비 (선택)
        
        # 처리 결과
        self.df_final_pivot = None
        self.df_tax_new = None
        self.filtered_df_book = None
        self.final_merged_df = None
        
    def load_all_data(self, file_paths: Dict[str, str]):
        """모든 Excel 파일 로드"""
        try:
            # 1. 기준 데이터 로드
            if 'standard' in file_paths:
                self.df_standard = read_excel_data(file_paths['standard'])
                print(f"기준 데이터 로드: {len(self.df_standard)}건")
            
            # 2. 협력사단품별매입 로드
            if 'purchase_detail' in file_paths:
                self.df = read_excel_data(file_paths['purchase_detail'], header=0)
                # Grand Total 행 제거 (노트북 로직)
                if len(self.df) > 0:
                    self.df = self.df.drop(0).reset_index(drop=True)
                print(f"협력사단품별매입 로드: {len(self.df)}건")
            
            # 3. 매입세금계산서 로드
            if 'tax_invoice' in file_paths:
                self.df_tax_hifi = read_excel_data(file_paths['tax_invoice'], header=[0,1])
                print(f"매입세금계산서 로드: {len(self.df_tax_hifi)}건")
            
            # 4. 지불보조장 로드
            if 'payment_book' in file_paths:
                self.df_book = read_excel_data(file_paths['payment_book'])
                print(f"지불보조장 로드: {len(self.df_book)}건")
            
            # 5. 매입세금계산서(WIS) 로드
            if 'tax_invoice_wis' in file_paths:
                self.df_num = read_excel_data(file_paths['tax_invoice_wis'])
                print(f"매입세금계산서(WIS) 로드: {len(self.df_num)}건")
            
            # 6. 임가공비 로드 (선택사항)
            if 'processing_fee' in file_paths and file_paths['processing_fee']:
                self.df_processing = read_excel_data(file_paths['processing_fee'])
                print(f"임가공비 로드: {len(self.df_processing)}건")
                
        except Exception as e:
            raise Exception(f"데이터 로드 실패: {str(e)}")
    
    def process_reconciliation(self, start_date: datetime, end_date: datetime) -> Dict:
        """매입대사 처리 - 노트북 로직 그대로 구현"""
        results = {
            'period': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d')
            },
            'summary': {},
            'output_path': None
        }
        
        try:
            # 1. 데이터 전처리 및 피벗
            self._preprocess_and_pivot()
            
            # 2. 세금계산서 데이터 처리
            self._process_tax_invoices()
            
            # 3. 대사 처리 (노트북의 복잡한 로직)
            self._process_matching()
            
            # 4. 지불보조장 대사
            self._process_payment_book()
            
            # 5. 최종 결과 생성
            self._create_final_results()
            
            # 6. Excel 파일 생성
            output_path = self._save_to_excel()
            results['output_path'] = output_path
            
            # 7. 요약 정보 생성
            results['summary'] = self._create_summary()
            
            return results
            
        except Exception as e:
            raise Exception(f"대사 처리 실패: {str(e)}")
    
    def _preprocess_and_pivot(self):
        """데이터 전처리 및 피벗 - 노트북 로직"""
        # 그룹화하여 최종매입금액 합계
        self.df_pivot = self.df.groupby(["년월", "협력사코드", "단품코드", "면과세구분명"]).agg({
            "최종매입금액": "sum",
            "협력사명": "first",
            "단품명": "first"
        }).reset_index()
        
        # 컬럼 순서 조정
        self.df_pivot = self.df_pivot[["년월", "협력사코드", "협력사명", "단품코드", "단품명", "면과세구분명", "최종매입금액"]]
        
        # 기준 데이터와 조인
        df_standard_subset = self.df_standard[['협력사코드', '단품코드']].drop_duplicates(subset=['협력사코드', '단품코드'])
        
        # 타입 변환
        self.df_pivot['협력사코드'] = self.df_pivot['협력사코드'].astype(int).astype(str)
        df_standard_subset['협력사코드'] = df_standard_subset['협력사코드'].astype(int).astype(str)
        self.df_pivot['단품코드'] = self.df_pivot['단품코드'].astype(int).astype(str)
        df_standard_subset['단품코드'] = df_standard_subset['단품코드'].astype(int).astype(str)
        
        # Inner join
        df_final = pd.merge(self.df_pivot, df_standard_subset, on=['협력사코드', '단품코드'], how='inner')
        
        # 협력사별 집계
        self.df_final_pivot = df_final.groupby(["년월", "협력사코드", "면과세구분명"]).agg({
            "협력사명": "first",
            "최종매입금액": "sum"
        }).reset_index()
        
        self.df_final_pivot = self.df_final_pivot[["년월", "협력사코드", "협력사명", "면과세구분명", "최종매입금액"]]
        
        # 정렬 및 key 생성
        self.df_final_pivot = self.df_final_pivot.sort_values(by=["협력사코드", "년월", "면과세구분명"])
        self.df_final_pivot["key"] = (
            self.df_final_pivot["년월"].astype(int).astype(str) + 
            self.df_final_pivot["협력사코드"].astype(str) + 
            self.df_final_pivot["면과세구분명"]
        )
        
        # 0원 제외
        self.df_final_pivot = self.df_final_pivot[self.df_final_pivot.최종매입금액 != 0]
    
    def _process_tax_invoices(self):
        """세금계산서 데이터 처리 - 노트북 로직"""
        # df_num에서 필요한 컬럼만 추출
        self.df_tax = self.df_num[[
            "협력사코드", "계산서작성일", "협력사명", "계산서구분", 
            "사업자번호", "공급가액", "세액", "국세청승인번호"
        ]]
        
        # 타입 변환
        self.df_final_pivot['협력사코드'] = self.df_final_pivot['협력사코드'].astype(str)
        self.df_tax['협력사코드'] = self.df_tax['협력사코드'].astype(str)
        
        # 필터링
        self.df_tax_sort = self.df_tax[self.df_tax.협력사코드.isin(self.df_final_pivot.협력사코드.tolist())]
        
        # df_tax_hifi 처리 (MultiIndex 헤더)
        self.df_tax_hifi.columns = [col[0] if pd.isna(col[1]) else f"{col[0]}_{col[1]}" for col in self.df_tax_hifi.columns]
        
        # 컬럼 매핑
        column_mapping = {
            '국세청승인번호': '국세청승인번호',
            '업체사업자번호': '업체사업자번호',
            '국세청작성일': 'nan_작성일',
            '국세청발급일': 'nan_발급일'
        }
        
        # lookup_df 생성
        lookup_df = self.df_tax_hifi[[
            column_mapping['국세청승인번호'],
            column_mapping['업체사업자번호'],
            column_mapping['국세청작성일'],
            column_mapping['국세청발급일']
        ]].drop_duplicates(subset=column_mapping['국세청승인번호'], keep='first')
        
        lookup_df = lookup_df.rename(columns={
            column_mapping['국세청승인번호']: '국세청승인번호',
            column_mapping['업체사업자번호']: '업체사업자번호',
            column_mapping['국세청작성일']: '국세청작성일',
            column_mapping['국세청발급일']: '국세청발급일'
        })
        
        # 병합
        self.df_tax_new = pd.merge(self.df_tax_sort, lookup_df, on='국세청승인번호', how='left')
        
        # 날짜 변환
        self.df_tax_new['국세청작성일'] = pd.to_datetime(self.df_tax_new['국세청작성일'], errors='coerce')
        self.df_tax_new['국세청발급일'] = pd.to_datetime(self.df_tax_new['국세청발급일'], errors='coerce')
        
        # 업체사업자번호 정리
        self.df_tax_new["업체사업자번호"] = self.df_tax_new["업체사업자번호"].astype(str).str.replace("-", "", regex=True)
    
    def _process_matching(self):
        """대사 처리 - 노트북의 복잡한 매칭 로직"""
        # 노트북 코드의 대사 로직을 그대로 이식
        # (코드가 너무 길어서 주요 부분만 표시)
        
        # 작성년도, 작성월 추출
        self.df_tax_new['작성년도'] = self.df_tax_new['국세청작성일'].dt.year
        self.df_tax_new['작성월'] = self.df_tax_new['국세청작성일'].dt.month
        
        # 공급가액, 세액 숫자 변환
        self.df_tax_new["공급가액"] = pd.to_numeric(self.df_tax_new["공급가액"], errors="coerce")
        self.df_tax_new["세액"] = pd.to_numeric(self.df_tax_new["세액"], errors="coerce")
        
        # 대사여부, 구분키 컬럼 추가
        self.df_tax_new['대사여부'] = ""
        self.df_tax_new['구분키'] = ""
        
        # df_final_pivot 처리
        self.df_final_pivot['년'] = self.df_final_pivot['년월'].astype(str).str[:4].astype(int)
        self.df_final_pivot['월'] = self.df_final_pivot['년월'].astype(str).str[4:6].astype(int)
        
        # 국세청 관련 컬럼 추가
        self.df_final_pivot['국세청작성일'] = None
        self.df_final_pivot['국세청발급일'] = None
        self.df_final_pivot['국세청공급가액'] = None
        self.df_final_pivot['국세청세액'] = None
        self.df_final_pivot['구분키'] = ""
        self.df_final_pivot['국세청승인번호'] = None
        self.df_final_pivot['업체사업자번호'] = None
        
        tolerance = 1e-6
        
        # Step A: 금액대사 (1:1 대사)
        self._process_exact_matching(tolerance)
        
        # Step A-2: 금액대사(수기확인)
        self._process_exact_matching_manual(tolerance)
        
        # Step B: 순차대사 (1:N 대사)
        self._process_sequential_matching(tolerance)
        
        # Step C: 부분대사
        self._process_partial_matching(tolerance)
        
        # Step D: 부분대사(수기확인)
        self._process_partial_matching_manual(tolerance)
    
    def _process_exact_matching(self, tolerance):
        """금액대사 (1:1 정확한 매칭)"""
        for idx, row in self.df_final_pivot.iterrows():
            협력사코드_final = row['협력사코드']
            년도_final = row['년']
            월_final = row['월']
            금액_final = row['최종매입금액']
            
            # 면과세구분에 따른 계산서구분
            if row['면과세구분명'] in ["과세", "영세"]:
                invoice_condition = "일반세금계산서"
            else:
                invoice_condition = "일반계산서"
            
            condition = (
                (self.df_tax_new['협력사코드'] == 협력사코드_final) &
                (self.df_tax_new['작성년도'] == 년도_final) &
                (self.df_tax_new['작성월'] == 월_final) &
                (self.df_tax_new['공급가액'] == 금액_final) &
                (self.df_tax_new['대사여부'] == "") &
                (self.df_tax_new['계산서구분'] == invoice_condition)
            )
            df_candidates = self.df_tax_new.loc[condition]
            
            if not df_candidates.empty:
                first_index = df_candidates.index[0]
                mapped_date = self.df_tax_new.at[first_index, '국세청작성일']
                mapped_issue_date = self.df_tax_new.at[first_index, '국세청발급일']
                mapped_supply = self.df_tax_new.at[first_index, '공급가액']
                mapped_tax = self.df_tax_new.at[first_index, '세액']
                
                self.df_final_pivot.at[idx, '국세청작성일'] = mapped_date
                self.df_final_pivot.at[idx, '국세청발급일'] = mapped_issue_date
                self.df_final_pivot.at[idx, '국세청공급가액'] = mapped_supply
                self.df_final_pivot.at[idx, '국세청세액'] = mapped_tax
                self.df_final_pivot.at[idx, '구분키'] = "금액대사"
                self.df_final_pivot.at[idx, '국세청승인번호'] = self.df_tax_new.at[first_index, '국세청승인번호']
                self.df_final_pivot.at[idx, '업체사업자번호'] = self.df_tax_new.at[first_index, '업체사업자번호']
                
                self.df_tax_new.at[first_index, '대사여부'] = f"{row['key']}-1"
                self.df_tax_new.at[first_index, '구분키'] = "금액대사"
    
    def _process_exact_matching_manual(self, tolerance):
        """금액대사(수기확인) - 면과세 조건 제외"""
        for idx, row in self.df_final_pivot.iterrows():
            if pd.notnull(row['국세청작성일']):
                continue
                
            협력사코드_final = row['협력사코드']
            년도_final = row['년']
            월_final = row['월']
            금액_final = row['최종매입금액']
            
            condition = (
                (self.df_tax_new['협력사코드'] == 협력사코드_final) &
                (self.df_tax_new['작성년도'] == 년도_final) &
                (self.df_tax_new['작성월'] == 월_final) &
                (self.df_tax_new['공급가액'] == 금액_final) &
                (self.df_tax_new['대사여부'] == "")
            )
            df_candidates = self.df_tax_new.loc[condition]
            
            if not df_candidates.empty:
                first_index = df_candidates.index[0]
                mapped_date = self.df_tax_new.at[first_index, '국세청작성일']
                mapped_issue_date = self.df_tax_new.at[first_index, '국세청발급일']
                mapped_supply = self.df_tax_new.at[first_index, '공급가액']
                mapped_tax = self.df_tax_new.at[first_index, '세액']
                
                self.df_final_pivot.at[idx, '국세청작성일'] = mapped_date
                self.df_final_pivot.at[idx, '국세청발급일'] = mapped_issue_date
                self.df_final_pivot.at[idx, '국세청공급가액'] = mapped_supply
                self.df_final_pivot.at[idx, '국세청세액'] = mapped_tax
                self.df_final_pivot.at[idx, '구분키'] = "금액대사(수기확인)"
                self.df_final_pivot.at[idx, '국세청승인번호'] = self.df_tax_new.at[first_index, '국세청승인번호']
                self.df_final_pivot.at[idx, '업체사업자번호'] = self.df_tax_new.at[first_index, '업체사업자번호']
                
                self.df_tax_new.at[first_index, '대사여부'] = f"{row['key']}-1"
                self.df_tax_new.at[first_index, '구분키'] = "금액대사(수기확인)"
    
    def _process_sequential_matching(self, tolerance):
        """순차대사 (1:N 매칭) - 노트북 로직에 따라 FIFO 방식으로 처리"""
        for idx, row in self.df_final_pivot.iterrows():
            if pd.notnull(row['국세청작성일']):
                continue
                
            협력사코드_final = row['협력사코드']
            년도_final = row['년']
            월_final = row['월']
            target_amount = row['최종매입금액']
            
            # 면과세구분에 따른 계산서구분
            if row['면과세구분명'] in ["과세", "영세"]:
                invoice_condition = "일반세금계산서"
            else:
                invoice_condition = "일반계산서"
            
            # 후보 찾기
            candidates = self.df_tax_new[
                (self.df_tax_new['협력사코드'] == 협력사코드_final) &
                (self.df_tax_new['작성년도'] == 년도_final) &
                (self.df_tax_new['작성월'] == 월_final) &
                (self.df_tax_new['대사여부'] == "") &
                (self.df_tax_new['계산서구분'] == invoice_condition)
            ]
            
            if candidates.empty:
                continue
            
            # 후보들을 국세청작성일 기준 오름차순(FIFO)로 정렬
            candidates = candidates.sort_values(by='국세청작성일')
            cumulative_sum = 0.0
            selected_indices = []
            
            # FIFO 방식으로 누적합 계산
            for cand_idx, cand_row in candidates.iterrows():
                cumulative_sum += cand_row['공급가액']
                selected_indices.append(cand_idx)
                
                # 누적합이 목표 금액과 일치하면 매칭
                if np.abs(cumulative_sum - target_amount) < tolerance:
                    # 날짜는 가장 빠른 것 사용
                    mapped_date = candidates.loc[selected_indices, '국세청작성일'].min()
                    mapped_issue_date = candidates.loc[selected_indices, '국세청발급일'].min()
                    mapped_supply = cumulative_sum
                    mapped_tax = candidates.loc[selected_indices, '세액'].sum()
                    
                    self.df_final_pivot.at[idx, '국세청작성일'] = mapped_date
                    self.df_final_pivot.at[idx, '국세청발급일'] = mapped_issue_date
                    self.df_final_pivot.at[idx, '국세청공급가액'] = mapped_supply
                    self.df_final_pivot.at[idx, '국세청세액'] = mapped_tax
                    self.df_final_pivot.at[idx, '구분키'] = "순차대사"
                    
                    # 첫 번째 매칭된 세금계산서 정보
                    first_idx = selected_indices[0]
                    self.df_final_pivot.at[idx, '국세청승인번호'] = candidates.loc[first_idx, '국세청승인번호']
                    self.df_final_pivot.at[idx, '업체사업자번호'] = candidates.loc[first_idx, '업체사업자번호']
                    
                    # 선택된 각 세금계산서에 대사여부 표시
                    for i, sel_idx in enumerate(selected_indices, start=1):
                        self.df_tax_new.at[sel_idx, '대사여부'] = f"{row['key']}-{i}"
                        self.df_tax_new.at[sel_idx, '구분키'] = f"순차대사-{i}"
                    break
            
            # FIFO로 안되면 부분집합 합 찾기 (백트래킹)
            else:
                found, indices = self._find_subset_sum_all_combinations(
                    candidates['공급가액'],
                    target_amount,
                    tolerance
                )
                
                if found and len(indices) > 0:
                    # 실제 인덱스로 변환
                    actual_indices = [candidates.index[idx] for idx in indices]
                    
                    # 첫 번째 매칭된 세금계산서 정보를 pivot에 기록
                    first_tax_idx = actual_indices[0]
                    mapped_date = self.df_tax_new.at[first_tax_idx, '국세청작성일']
                    mapped_issue_date = self.df_tax_new.at[first_tax_idx, '국세청발급일']
                    
                    # 합계 계산
                    total_supply = sum(self.df_tax_new.at[idx, '공급가액'] for idx in actual_indices)
                    total_tax = sum(self.df_tax_new.at[idx, '세액'] for idx in actual_indices)
                    
                    self.df_final_pivot.at[idx, '국세청작성일'] = mapped_date
                    self.df_final_pivot.at[idx, '국세청발급일'] = mapped_issue_date
                    self.df_final_pivot.at[idx, '국세청공급가액'] = total_supply
                    self.df_final_pivot.at[idx, '국세청세액'] = total_tax
                    self.df_final_pivot.at[idx, '구분키'] = "순차대사"
                    self.df_final_pivot.at[idx, '국세청승인번호'] = self.df_tax_new.at[first_tax_idx, '국세청승인번호']
                    self.df_final_pivot.at[idx, '업체사업자번호'] = self.df_tax_new.at[first_tax_idx, '업체사업자번호']
                    
                    # 선택된 각 세금계산서에 대사여부 표시
                    for i, actual_idx in enumerate(actual_indices, start=1):
                        self.df_tax_new.at[actual_idx, '대사여부'] = f"{row['key']}-{i}"
                        self.df_tax_new.at[actual_idx, '구분키'] = f"순차대사-{i}"
    
    def _process_partial_matching(self, tolerance):
        """부분대사 - 금액이 더 큰 세금계산서와 1:1 매칭"""
        for idx, row in self.df_final_pivot.iterrows():
            if pd.notnull(row['국세청작성일']):
                continue
                
            협력사코드_final = row['협력사코드']
            년도_final = row['년']
            월_final = row['월']
            target_amount = row['최종매입금액']
            
            # 면과세구분에 따른 계산서구분
            if row['면과세구분명'] in ["과세", "영세"]:
                invoice_condition = "일반세금계산서"
            else:
                invoice_condition = "일반계산서"
            
            # 후보 찾기: 공급가액이 target_amount보다 큰 경우
            candidates = self.df_tax_new[
                (self.df_tax_new['협력사코드'] == 협력사코드_final) &
                (self.df_tax_new['작성년도'] == 년도_final) &
                (self.df_tax_new['작성월'] == 월_final) &
                (self.df_tax_new['대사여부'] == "") &
                (self.df_tax_new['계산서구분'] == invoice_condition) &
                (self.df_tax_new['공급가액'] > target_amount)
            ]
            
            if candidates.empty:
                continue
                
            # 국세청발급일이 가장 빠른 것 선택 (오름차순 정렬)
            candidates = candidates.sort_values(by='국세청발급일', ascending=True)
            
            # 첫 번째 후보 선택
            candidate_index = candidates.index[0]
            candidate_row = candidates.loc[candidate_index]
            
            # 매핑
            mapped_date = candidate_row['국세청작성일']
            mapped_issue_date = candidate_row['국세청발급일']
            mapped_supply = candidate_row['공급가액']
            mapped_tax = candidate_row['세액']
            
            self.df_final_pivot.at[idx, '국세청작성일'] = mapped_date
            self.df_final_pivot.at[idx, '국세청발급일'] = mapped_issue_date
            self.df_final_pivot.at[idx, '국세청공급가액'] = mapped_supply
            self.df_final_pivot.at[idx, '국세청세액'] = mapped_tax
            self.df_final_pivot.at[idx, '구분키'] = "부분대사"
            self.df_final_pivot.at[idx, '국세청승인번호'] = candidate_row['국세청승인번호']
            self.df_final_pivot.at[idx, '업체사업자번호'] = candidate_row['업체사업자번호']
            
            # 1:1 매칭이므로 번호는 -1로 표시
            self.df_tax_new.at[candidate_index, '대사여부'] = f"{row['key']}-1"
            self.df_tax_new.at[candidate_index, '구분키'] = "부분대사"
    
    def _process_partial_matching_manual(self, tolerance):
        """부분대사(수기확인) - 여러 후보 합산 후 매칭"""
        for idx, row in self.df_final_pivot.iterrows():
            if pd.notnull(row['국세청작성일']):
                continue
                
            협력사코드_final = row['협력사코드']
            년도_final = row['년']
            월_final = row['월']
            target_amount = row['최종매입금액']
            
            # 면과세구분에 따른 계산서구분
            if row['면과세구분명'] in ["과세", "영세"]:
                invoice_condition = "일반세금계산서"
            else:
                invoice_condition = "일반계산서"
            
            # 후보 찾기: 공급가액이 target_amount 이하인 경우
            candidates = self.df_tax_new[
                (self.df_tax_new['협력사코드'] == 협력사코드_final) &
                (self.df_tax_new['작성년도'] == 년도_final) &
                (self.df_tax_new['작성월'] == 월_final) &
                (self.df_tax_new['대사여부'] == "") &
                (self.df_tax_new['계산서구분'] == invoice_condition)
            ]
            candidates = candidates[candidates['공급가액'] <= target_amount]
            
            if candidates.empty:
                continue
                
            # 국세청발급일이 늦은 순으로 정렬 (오름차순)
            candidates = candidates.sort_values(by='국세청발급일', ascending=True)
            
            cumulative_sum = 0.0
            selected_indices = []
            
            # 누적 합이 target_amount를 초과할 때까지 선택
            for cand_idx, cand_row in candidates.iterrows():
                cumulative_sum += cand_row['공급가액']
                selected_indices.append(cand_idx)
                if cumulative_sum > target_amount:
                    break
            
            # 누적 합이 target_amount보다 큰 경우에만 매칭
            if cumulative_sum > target_amount and len(selected_indices) > 0:
                # 대표 날짜는 가장 늦은 날짜로 설정
                representative_date = candidates.loc[selected_indices, '국세청작성일'].max()
                representative_issue_date = candidates.loc[selected_indices, '국세청발급일'].max()
                mapped_supply = cumulative_sum
                mapped_tax = candidates.loc[selected_indices, '세액'].sum()
                
                self.df_final_pivot.at[idx, '국세청작성일'] = representative_date
                self.df_final_pivot.at[idx, '국세청발급일'] = representative_issue_date
                self.df_final_pivot.at[idx, '국세청공급가액'] = mapped_supply
                self.df_final_pivot.at[idx, '국세청세액'] = mapped_tax
                self.df_final_pivot.at[idx, '구분키'] = "수기확인"
                
                # 첫 번째 매칭된 것의 정보 사용
                first_idx = selected_indices[0]
                self.df_final_pivot.at[idx, '국세청승인번호'] = candidates.loc[first_idx, '국세청승인번호']
                self.df_final_pivot.at[idx, '업체사업자번호'] = candidates.loc[first_idx, '업체사업자번호']
                
                # 선택된 각 세금계산서에 대사여부 표시
                for i, sel_idx in enumerate(selected_indices, start=1):
                    self.df_tax_new.at[sel_idx, '대사여부'] = f"{row['key']}-{i}"
                    self.df_tax_new.at[sel_idx, '구분키'] = f"수기확인-{i}"
    
    def _find_subset_sum_all_combinations(self, amounts, target, tolerance=1e-6):
        """
        부분집합의 합이 target과 일치하는 인덱스 찾기
        DFS를 사용한 백트래킹 구현
        
        amounts: 금액이 들어있는 Series
        target: 목표 금액
        tolerance: float 비교를 위한 허용 오차
        반환값: (True, [인덱스 리스트]) 또는 (False, [])
        """
        # Series를 (인덱스, 금액) 튜플 리스트로 변환
        candidate_items = [(idx, amt) for idx, amt in amounts.items()]
        result_container = {'found': False, 'indices': []}
        
        def dfs(start_idx, current_sum, chosen_indices):
            if result_container['found']:
                return
            if np.abs(current_sum - target) < tolerance:
                result_container['found'] = True
                result_container['indices'] = chosen_indices[:]
                return
            if start_idx >= len(candidate_items):
                return
            if current_sum > target:
                return
                
            # 현재 원소 포함
            cand_idx, cand_amt = candidate_items[start_idx]
            dfs(start_idx + 1, current_sum + cand_amt, chosen_indices + [cand_idx])
            # 현재 원소 미포함
            dfs(start_idx + 1, current_sum, chosen_indices)
            
        dfs(0, 0.0, [])
        return (True, result_container['indices']) if result_container['found'] else (False, [])
    
    def _process_payment_book(self):
        """지불보조장 대사"""
        # 거래처번호 변환
        def convert_vendor_to_string(val):
            if pd.isna(val):
                return ''
            elif isinstance(val, (int, float)):
                return str(int(val))
            else:
                return str(val)
        
        self.df_book['거래처번호'] = self.df_book['거래처번호'].apply(convert_vendor_to_string)
        
        # 필터링
        self.filtered_df_book = self.df_book[
            self.df_book['거래처번호'].isin(self.df_final_pivot['업체사업자번호'])
        ]
        
        if not self.filtered_df_book.empty:
            self.filtered_df_book = self.filtered_df_book[[
                "계정코드", "계정과목명", "회계일", "전표번호", 
                "거래처번호", "거래처명", "차변금액", "대변금액"
            ]]
            
            # 차변금액, 대변금액 변환
            self.filtered_df_book["차변금액"] = self.filtered_df_book["차변금액"].str.replace(",", "", regex=True).astype(float)
            self.filtered_df_book["대변금액"] = self.filtered_df_book["대변금액"].str.replace(",", "", regex=True).astype(float)
            self.filtered_df_book = self.filtered_df_book[self.filtered_df_book['차변금액'] != 0]
        
        # 지불예상금액 계산
        self.df_final_pivot["지불예상금액"] = self.df_final_pivot["국세청공급가액"] + self.df_final_pivot["국세청세액"]
    
    def _create_final_results(self):
        """최종 결과 생성"""
        # 최종지불금액 계산
        self.df_final_pivot['최종지불금액'] = self.df_final_pivot['최종매입금액']
        
        # 과세: 최종매입금액에 1.1을 곱함
        mask_taxable = self.df_final_pivot['면과세구분명'] == '과세'
        self.df_final_pivot.loc[mask_taxable, '최종지불금액'] = self.df_final_pivot.loc[mask_taxable, '최종매입금액'] * 1.1
        
        # 정렬
        self.df_final_pivot = self.df_final_pivot.sort_values(by=["업체사업자번호", "협력사코드", "년월"], ascending=True)
        
        # 최종 DataFrame
        self.final_merged_df = self.df_final_pivot[[
            "협력사코드", "협력사명", '년월', '면과세구분명', '최종매입금액', 
            '구분키', 'key', '업체사업자번호', '최종지불금액', '지불예상금액'
        ]]
    
    def _save_to_excel(self):
        """Excel 파일 저장 - 노트북과 동일한 형식"""
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"매입대사결과_{timestamp}.xlsx"
        
        # 시트 데이터 준비
        sheets_data = [
            ("최종총괄장내역", self.final_merged_df),
            ("대사총괄장내역", self.df_final_pivot),
            ("지불보조장내역", self.filtered_df_book if hasattr(self, 'filtered_df_book') else pd.DataFrame()),
            ("세금계산서내역", self.df_tax_new),
            ("요청단품내역", self.df_standard)
        ]
        
        # Excel 파일 생성 (노트북의 save_excel_with_pywin 함수와 유사)
        self._save_excel_with_pywin(str(output_path), sheets_data)
        
        return str(output_path)
    
    def _save_excel_with_pywin(self, save_path, sheets_data):
        """win32com을 사용한 Excel 저장"""
        excel = win32.Dispatch("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False
        
        wb = excel.Workbooks.Add()
        
        # 첫 번째 시트
        first_sheet_name, first_df = sheets_data[0]
        ws = wb.Worksheets(1)
        ws.Name = first_sheet_name
        self._df_to_sheet(ws, first_df)
        
        # 나머지 시트
        for sheet_name, df in sheets_data[1:]:
            ws = wb.Worksheets.Add(After=wb.Worksheets(wb.Worksheets.Count))
            ws.Name = sheet_name
            self._df_to_sheet(ws, df)
        
        # 저장
        wb.SaveAs(os.path.abspath(save_path), FileFormat=51)
        wb.Close(False)
        excel.Quit()
    
    def _df_to_sheet(self, sheet, df, start_row=1, start_col=1):
        """DataFrame을 Excel 시트에 기록"""
        if df.empty:
            return
            
        n_rows, n_cols = df.shape
        
        # 헤더 작성
        for col_idx, col_name in enumerate(df.columns.values, start=start_col):
            sheet.Cells(start_row, col_idx).Value = col_name
        
        # 데이터 작성
        for row_idx in range(n_rows):
            for col_idx in range(n_cols):
                val = df.iat[row_idx, col_idx]
                if pd.isnull(val):
                    val = ""
                elif isinstance(val, pd.Timestamp):
                    if val.tzinfo is None:
                        val = val.tz_localize("UTC").to_pydatetime()
                    else:
                        val = val.to_pydatetime()
                sheet.Cells(start_row + row_idx + 1, col_idx + start_col).Value = val
        
        # 스타일 적용
        self._apply_styles(sheet, n_rows + 1, n_cols)
    
    def _apply_styles(self, sheet, last_row, last_col):
        """Excel 스타일 적용"""
        used_range = sheet.Range(sheet.Cells(1, 1), sheet.Cells(last_row, last_col))
        used_range.Borders.LineStyle = 1  # 얇은 테두리
        
        # 헤더 스타일
        header_range = sheet.Range(sheet.Cells(1, 1), sheet.Cells(1, last_col))
        header_range.Font.Bold = True
        header_range.HorizontalAlignment = -4108  # xlCenter
        header_range.VerticalAlignment = -4108
        header_range.Interior.Color = 0xD3D3D3  # 회색
        
        # 열 너비 자동 조정
        sheet.Columns.AutoFit()
    
    def _create_summary(self):
        """요약 정보 생성"""
        summary = {
            'total_count': len(self.df_final_pivot),
            'exact_match': len(self.df_final_pivot[self.df_final_pivot['구분키'] == '금액대사']),
            'sequential_match': len(self.df_final_pivot[self.df_final_pivot['구분키'] == '순차대사']),
            'partial_match': len(self.df_final_pivot[self.df_final_pivot['구분키'] == '부분대사']),
            'unmatched': len(self.df_final_pivot[self.df_final_pivot['구분키'] == ''])
        }
        
        return summary

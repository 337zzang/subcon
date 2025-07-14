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
        errors = []
        loaded_files = []
        
        # 필수 파일 체크
        required_files = ['standard', 'purchase_detail', 'tax_invoice', 'payment_ledger', 'tax_invoice_wis']
        missing_files = [f for f in required_files if f not in file_paths or not file_paths[f]]
        
        if missing_files:
            raise ValueError(f"필수 파일이 누락되었습니다: {', '.join(missing_files)}")
        
        try:
            # 1. 기준 데이터 로드
            if 'standard' in file_paths:
                try:
                    self.df_standard = read_excel_data(file_paths['standard'])
                    if self.df_standard is None or len(self.df_standard) == 0:
                        raise ValueError("기준 데이터가 비어있습니다")
                    print(f"기준 데이터 로드: {len(self.df_standard)}건")
                    loaded_files.append('standard')
                except Exception as e:
                    errors.append(f"기준 파일 로드 오류: {str(e)}")
                    raise
            
            # 2. 협력사단품별매입 로드
            if 'purchase_detail' in file_paths:
                try:
                    self.df = read_excel_data(file_paths['purchase_detail'], header=0)
                    # Grand Total 행 제거 (노트북 로직)
                    if len(self.df) > 0:
                        self.df = self.df.drop(0).reset_index(drop=True)
                    if self.df is None or len(self.df) == 0:
                        raise ValueError("협력사단품별매입 데이터가 비어있습니다")
                    print(f"협력사단품별매입 로드: {len(self.df)}건")
                    loaded_files.append('purchase_detail')
                except Exception as e:
                    errors.append(f"협력사단품별매입 파일 로드 오류: {str(e)}")
                    raise
            
            # 3. 매입세금계산서 로드
            if 'tax_invoice' in file_paths:
                try:
                    self.df_tax_hifi = read_excel_data(file_paths['tax_invoice'], header=[0,1])
                    if self.df_tax_hifi is None or len(self.df_tax_hifi) == 0:
                        raise ValueError("매입세금계산서 데이터가 비어있습니다")
                    print(f"매입세금계산서 로드: {len(self.df_tax_hifi)}건")
                    loaded_files.append('tax_invoice')
                except Exception as e:
                    errors.append(f"매입세금계산서 파일 로드 오류: {str(e)}")
                    raise
            
            # 4. 지불보조장 로드
            if 'payment_ledger' in file_paths:
                try:
                    self.df_book = read_excel_data(file_paths['payment_ledger'])
                    if self.df_book is None or len(self.df_book) == 0:
                        raise ValueError("지불보조장 데이터가 비어있습니다")
                    print(f"지불보조장 로드: {len(self.df_book)}건")
                    loaded_files.append('payment_ledger')
                except Exception as e:
                    errors.append(f"지불보조장 파일 로드 오류: {str(e)}")
                    raise
            
            # 5. 매입세금계산서(WIS) 로드
            if 'tax_invoice_wis' in file_paths:
                try:
                    self.df_num = read_excel_data(file_paths['tax_invoice_wis'])
                    if self.df_num is None or len(self.df_num) == 0:
                        raise ValueError("매입세금계산서(WIS) 데이터가 비어있습니다")
                    print(f"매입세금계산서(WIS) 로드: {len(self.df_num)}건")
                    loaded_files.append('tax_invoice_wis')
                except Exception as e:
                    errors.append(f"매입세금계산서(WIS) 파일 로드 오류: {str(e)}")
                    raise
            
            # 6. 임가공비 로드 (선택사항)
            if 'processing_fee' in file_paths and file_paths['processing_fee']:
                try:
                    self.df_processing = read_excel_data(file_paths['processing_fee'])
                    print(f"임가공비 로드: {len(self.df_processing)}건")
                    loaded_files.append('processing_fee')
                except Exception as e:
                    print(f"임가공비 파일 로드 경고: {str(e)} (선택 파일이므로 계속 진행)")
                    
            print(f"\n✅ 파일 로드 완료: {len(loaded_files)}개 파일")
                
        except Exception as e:
            if errors:
                error_msg = "데이터 로드 중 오류 발생:\n" + "\n".join(errors)
            else:
                error_msg = f"데이터 로드 실패: {str(e)}"
            raise Exception(error_msg)
    
    def process_reconciliation(self, start_date: datetime, end_date: datetime) -> Dict:
        """매입대사 처리 - 노트북 로직 그대로 구현"""
        results = {
            'period': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d')
            },
            'summary': {},
            'output_path': None,
            'errors': [],
            'warnings': []
        }
        
        try:
            # 0. 날짜 유효성 검증
            if start_date > end_date:
                raise ValueError(f"시작일({start_date})이 종료일({end_date})보다 늦습니다")
            
            # 1. 데이터 전처리 및 피벗
            print("📊 데이터 전처리 시작...")
            try:
                self._preprocess_and_pivot()
                print(f"✅ 피벗 데이터 생성 완료: {len(self.df_final_pivot)}건")
            except Exception as e:
                raise Exception(f"데이터 전처리 실패: {str(e)}")
            
            # 2. 세금계산서 데이터 처리
            print("📄 세금계산서 데이터 처리 시작...")
            try:
                self._process_tax_invoices()
                print(f"✅ 세금계산서 처리 완료: {len(self.df_tax_new)}건")
            except Exception as e:
                raise Exception(f"세금계산서 처리 실패: {str(e)}")
            
            # 3. 대사 처리 (노트북의 복잡한 로직)
            print("🔄 대사 처리 시작...")
            try:
                self._process_matching()
                print("✅ 대사 처리 완료")
            except Exception as e:
                raise Exception(f"대사 처리 실패: {str(e)}")
            
            # 4. 지불보조장 대사
            print("💳 지불보조장 대사 시작...")
            try:
                self._process_payment_book()
                if hasattr(self, 'filtered_df_book'):
                    print(f"✅ 지불보조장 대사 완료: {len(self.filtered_df_book)}건")
            except Exception as e:
                results['warnings'].append(f"지불보조장 대사 경고: {str(e)}")
                print(f"⚠️ 지불보조장 대사 경고: {str(e)}")
            
            # 5. 최종 결과 생성
            print("📝 최종 결과 생성...")
            try:
                self._create_final_results()
                print("✅ 최종 결과 생성 완료")
            except Exception as e:
                raise Exception(f"최종 결과 생성 실패: {str(e)}")
            
            # 6. Excel 파일 생성
            print("💾 Excel 파일 생성...")
            try:
                output_path = self._save_to_excel()
                results['output_path'] = output_path
                print(f"✅ Excel 파일 생성 완료: {output_path}")
            except Exception as e:
                raise Exception(f"Excel 파일 생성 실패: {str(e)}")
            
            # 7. 요약 정보 생성
            try:
                results['summary'] = self._create_summary()
                
                # 검증 결과 확인
                validation = results['summary'].get('validation', {})
                if validation.get('errors'):
                    results['errors'].extend(validation['errors'])
                if validation.get('warnings'):
                    results['warnings'].extend(validation['warnings'])
                    
            except Exception as e:
                results['warnings'].append(f"요약 정보 생성 경고: {str(e)}")
            
            return results
            
        except Exception as e:
            results['errors'].append(str(e))
            results['summary'] = {'status': 'failed', 'error': str(e)}
            raise Exception(f"대사 처리 실패: {str(e)}")
    
    def _preprocess_and_pivot(self):
        """데이터 전처리 및 피벗 - 노트북 로직"""
        try:
            # 필수 데이터 확인
            if self.df is None or len(self.df) == 0:
                raise ValueError("협력사단품별매입 데이터가 없습니다")
            if self.df_standard is None or len(self.df_standard) == 0:
                raise ValueError("기준 데이터가 없습니다")
                
            # 필수 컬럼 확인
            required_cols = ["년월", "협력사코드", "단품코드", "면과세구분명", "최종매입금액", "협력사명", "단품명"]
            missing_cols = [col for col in required_cols if col not in self.df.columns]
            if missing_cols:
                raise ValueError(f"협력사단품별매입 파일에 필수 컬럼이 없습니다: {', '.join(missing_cols)}")
            
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
            try:
                self.df_pivot['협력사코드'] = self.df_pivot['협력사코드'].astype(int).astype(str)
                df_standard_subset['협력사코드'] = df_standard_subset['협력사코드'].astype(int).astype(str)
                self.df_pivot['단품코드'] = self.df_pivot['단품코드'].astype(int).astype(str)
                df_standard_subset['단품코드'] = df_standard_subset['단품코드'].astype(int).astype(str)
            except Exception as e:
                raise ValueError(f"협력사코드/단품코드 타입 변환 실패: {str(e)}")
            
            # Inner join
            df_final = pd.merge(self.df_pivot, df_standard_subset, on=['협력사코드', '단품코드'], how='inner')
            
            if len(df_final) == 0:
                raise ValueError("기준 데이터와 매칭되는 데이터가 없습니다")
            
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
            
            if len(self.df_final_pivot) == 0:
                raise ValueError("처리할 데이터가 없습니다 (모든 금액이 0원)")
                
        except Exception as e:
            raise Exception(f"데이터 전처리 실패: {str(e)}")
    
    def _process_tax_invoices(self):
        """세금계산서 데이터 처리 - 노트북 로직"""
        try:
            # 필수 데이터 확인
            if self.df_num is None or len(self.df_num) == 0:
                raise ValueError("매입세금계산서(WIS) 데이터가 없습니다")
            if self.df_tax_hifi is None or len(self.df_tax_hifi) == 0:
                raise ValueError("매입세금계산서 데이터가 없습니다")
                
            # df_num에서 필요한 컬럼 확인
            required_cols = ["협력사코드", "계산서작성일", "협력사명", "계산서구분", 
                           "사업자번호", "공급가액", "세액", "국세청승인번호"]
            missing_cols = [col for col in required_cols if col not in self.df_num.columns]
            if missing_cols:
                raise ValueError(f"매입세금계산서(WIS)에 필수 컬럼이 없습니다: {', '.join(missing_cols)}")
            
            # df_num에서 필요한 컬럼만 추출
            self.df_tax = self.df_num[required_cols]
            
            # 타입 변환
            try:
                self.df_final_pivot['협력사코드'] = self.df_final_pivot['협력사코드'].astype(str)
                self.df_tax['협력사코드'] = self.df_tax['협력사코드'].astype(str)
            except Exception as e:
                raise ValueError(f"협력사코드 타입 변환 실패: {str(e)}")
            
            # 필터링
            self.df_tax_sort = self.df_tax[self.df_tax.협력사코드.isin(self.df_final_pivot.협력사코드.tolist())]
            
            if len(self.df_tax_sort) == 0:
                raise ValueError("매칭되는 세금계산서가 없습니다")
            
            # df_tax_hifi 처리 (MultiIndex 헤더)
            try:
                self.df_tax_hifi.columns = [col[0] if pd.isna(col[1]) else f"{col[0]}_{col[1]}" for col in self.df_tax_hifi.columns]
            except Exception as e:
                raise ValueError(f"매입세금계산서 헤더 처리 실패: {str(e)}")
            
            # 컬럼 매핑
            column_mapping = {
                '국세청승인번호': '국세청승인번호',
                '업체사업자번호': '업체사업자번호',
                '국세청작성일': 'nan_작성일',
                '국세청발급일': 'nan_발급일'
            }
            
            # lookup_df 생성
            try:
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
            except KeyError as e:
                # 컬럼명이 다를 수 있으므로 대체 시도
                print(f"⚠️ 컬럼 매핑 경고: {str(e)}")
                # 컬럼명 확인 후 재시도
                available_cols = list(self.df_tax_hifi.columns)
                print(f"사용 가능한 컬럼: {available_cols[:10]}...")  # 처음 10개만 표시
                
                # 대체 매핑 시도
                lookup_df = pd.DataFrame()  # 빈 DataFrame으로 초기화
            
            # 병합
            if not lookup_df.empty:
                self.df_tax_new = pd.merge(self.df_tax_sort, lookup_df, on='국세청승인번호', how='left')
            else:
                self.df_tax_new = self.df_tax_sort.copy()
                self.df_tax_new['국세청작성일'] = None
                self.df_tax_new['국세청발급일'] = None
                self.df_tax_new['업체사업자번호'] = self.df_tax_new['사업자번호']
            
            # 날짜 변환
            try:
                self.df_tax_new['국세청작성일'] = pd.to_datetime(self.df_tax_new['국세청작성일'], errors='coerce')
                self.df_tax_new['국세청발급일'] = pd.to_datetime(self.df_tax_new['국세청발급일'], errors='coerce')
            except Exception as e:
                print(f"⚠️ 날짜 변환 경고: {str(e)}")
            
            # 업체사업자번호 정리
            self.df_tax_new["업체사업자번호"] = self.df_tax_new["업체사업자번호"].astype(str).str.replace("-", "", regex=True)
            
        except Exception as e:
            raise Exception(f"세금계산서 데이터 처리 실패: {str(e)}")
    
    def _process_matching(self):
        """대사 처리 - 노트북의 복잡한 매칭 로직"""
        try:
            # 필수 데이터 확인
            if self.df_tax_new is None or len(self.df_tax_new) == 0:
                raise ValueError("세금계산서 데이터가 없습니다")
            if self.df_final_pivot is None or len(self.df_final_pivot) == 0:
                raise ValueError("피벗 데이터가 없습니다")
            
            # 작성년도, 작성월 추출
            try:
                self.df_tax_new['작성년도'] = self.df_tax_new['국세청작성일'].dt.year
                self.df_tax_new['작성월'] = self.df_tax_new['국세청작성일'].dt.month
            except Exception as e:
                # 국세청작성일이 없는 경우 계산서작성일 사용
                print(f"⚠️ 국세청작성일 사용 불가, 계산서작성일 사용: {str(e)}")
                self.df_tax_new['계산서작성일'] = pd.to_datetime(self.df_tax_new['계산서작성일'], errors='coerce')
                self.df_tax_new['작성년도'] = self.df_tax_new['계산서작성일'].dt.year
                self.df_tax_new['작성월'] = self.df_tax_new['계산서작성일'].dt.month
            
            # 공급가액, 세액 숫자 변환
            try:
                self.df_tax_new["공급가액"] = pd.to_numeric(self.df_tax_new["공급가액"], errors="coerce")
                self.df_tax_new["세액"] = pd.to_numeric(self.df_tax_new["세액"], errors="coerce")
            except Exception as e:
                raise ValueError(f"금액 변환 실패: {str(e)}")
            
            # 대사여부, 구분키 컬럼 추가
            self.df_tax_new['대사여부'] = ""
            self.df_tax_new['구분키'] = ""
            
            # df_final_pivot 처리
            try:
                self.df_final_pivot['년'] = self.df_final_pivot['년월'].astype(str).str[:4].astype(int)
                self.df_final_pivot['월'] = self.df_final_pivot['년월'].astype(str).str[4:6].astype(int)
            except Exception as e:
                raise ValueError(f"년월 분리 실패: {str(e)}")
            
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
            try:
                self._process_exact_matching(tolerance)
                matched_count = len(self.df_final_pivot[self.df_final_pivot['구분키'] == '금액대사'])
                print(f"  - 금액대사 완료: {matched_count}건")
            except Exception as e:
                print(f"⚠️ 금액대사 경고: {str(e)}")
            
            # Step A-2: 금액대사(수기확인)
            try:
                self._process_exact_matching_manual(tolerance)
                matched_count = len(self.df_final_pivot[self.df_final_pivot['구분키'] == '금액대사(수기확인)'])
                print(f"  - 금액대사(수기확인) 완료: {matched_count}건")
            except Exception as e:
                print(f"⚠️ 금액대사(수기확인) 경고: {str(e)}")
            
            # Step B: 순차대사 (1:N 대사)
            try:
                self._process_sequential_matching(tolerance)
                matched_count = len(self.df_final_pivot[self.df_final_pivot['구분키'] == '순차대사'])
                print(f"  - 순차대사 완료: {matched_count}건")
            except Exception as e:
                print(f"⚠️ 순차대사 경고: {str(e)}")
            
            # Step C: 부분대사
            try:
                self._process_partial_matching(tolerance)
                matched_count = len(self.df_final_pivot[self.df_final_pivot['구분키'] == '부분대사'])
                print(f"  - 부분대사 완료: {matched_count}건")
            except Exception as e:
                print(f"⚠️ 부분대사 경고: {str(e)}")
            
            # Step D: 부분대사(수기확인)
            try:
                self._process_partial_matching_manual(tolerance)
                matched_count = len(self.df_final_pivot[self.df_final_pivot['구분키'] == '수기확인'])
                print(f"  - 부분대사(수기확인) 완료: {matched_count}건")
            except Exception as e:
                print(f"⚠️ 부분대사(수기확인) 경고: {str(e)}")
                
            # 전체 대사 결과 요약
            total_count = len(self.df_final_pivot)
            matched_total = len(self.df_final_pivot[self.df_final_pivot['구분키'] != ''])
            print(f"  - 전체 대사율: {matched_total}/{total_count} ({matched_total/total_count*100:.1f}%)")
            
        except Exception as e:
            raise Exception(f"대사 처리 실패: {str(e)}")
    
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
            
            # match_tax_and_book 로직 적용
            self._process_payment_book_matching()
        
        # 지불예상금액 계산
        # NaN 값을 0으로 채우고 계산
        self.df_final_pivot["국세청공급가액"] = self.df_final_pivot["국세청공급가액"].fillna(0)
        self.df_final_pivot["국세청세액"] = self.df_final_pivot["국세청세액"].fillna(0)
        self.df_final_pivot["지불예상금액"] = self.df_final_pivot["국세청공급가액"] + self.df_final_pivot["국세청세액"]
    
    def _process_payment_book_matching(self, tolerance=1e-6):
        """
        세금계산서(df_tax_new)와 지불보조장(filtered_df_book) 대사
        노트북의 match_tax_and_book 함수 로직 이식
        """
        # 필요한 컬럼 생성
        if '구분키2' not in self.df_tax_new.columns:
            self.df_tax_new['구분키2'] = None
        if '차변금액' not in self.df_tax_new.columns:
            self.df_tax_new['차변금액'] = None
        if '전표번호' not in self.df_tax_new.columns:
            self.df_tax_new['전표번호'] = None
        if '회계일' not in self.df_tax_new.columns:
            self.df_tax_new['회계일'] = None
        if '비고' not in self.df_tax_new.columns:
            self.df_tax_new['비고'] = ""
            
        # filtered_df_book에 필요한 컬럼 생성
        if '구분키' not in self.filtered_df_book.columns:
            self.filtered_df_book['구분키'] = ""
        if 'Key' not in self.filtered_df_book.columns:
            self.filtered_df_book['Key'] = None
            
        # 회계일 datetime 변환
        if not pd.api.types.is_datetime64_any_dtype(self.filtered_df_book['회계일']):
            self.filtered_df_book['회계일'] = pd.to_datetime(self.filtered_df_book['회계일'], errors='coerce')
            
        # 각 세금계산서에 대해 매칭 처리
        for idx, tax_row in self.df_tax_new.iterrows():
            # 이미 대사처리된 경우 건너뛰기
            if tax_row['구분키'] in [None, "", np.nan]:
                continue
            if tax_row['구분키2'] not in [None, "", np.nan]:
                continue
                
            # 대사금액 계산: 공급가액 + 세액
            pivot_amount = tax_row['공급가액'] + tax_row['세액']
            pivot_biz = tax_row['업체사업자번호']
            pivot_year = tax_row['작성년도']
            pivot_month = tax_row['작성월']
            
            # 허용 회계일 범위: pivot_month의 1일부터 +2개월 마지막 날까지
            allowed_lower = pd.Timestamp(pivot_year, pivot_month, 1)
            allowed_upper = allowed_lower + pd.DateOffset(months=2) - pd.DateOffset(days=1)
            
            # 후보 필터링
            candidates = self.filtered_df_book[
                (self.filtered_df_book['거래처번호'] == pivot_biz) &
                (self.filtered_df_book['구분키'] == "") &
                (self.filtered_df_book['회계일'] >= allowed_lower) &
                (self.filtered_df_book['회계일'] <= allowed_upper)
            ]
            
            if candidates.empty:
                continue
                
            # 회계일 기준 오름차순 정렬
            candidates = candidates.sort_values(by='회계일')
            
            # 1) 1:1 매칭 시도
            exact_match = candidates[np.abs(candidates['차변금액'] - pivot_amount) < tolerance]
            if not exact_match.empty:
                candidate_index = exact_match.index[0]
                candidate_row = candidates.loc[candidate_index]
                
                self.df_tax_new.at[idx, '구분키2'] = "매입금액대사"
                self.df_tax_new.at[idx, '차변금액'] = candidate_row['차변금액']
                self.df_tax_new.at[idx, '전표번호'] = candidate_row['전표번호']
                self.df_tax_new.at[idx, '회계일'] = candidate_row['회계일'].strftime("%Y-%m-%d")
                
                # filtered_df_book 업데이트
                self.filtered_df_book.at[candidate_index, 'Key'] = tax_row['대사여부']
                self.filtered_df_book.at[candidate_index, '구분키'] = "매입금액대사"
                continue
                
            # 2) 1:1 매칭 실패 시, 부분조합(매입순차대사(조합)) 매칭 시도
            subset_found, subset_indices = self._find_subset_sum_all_combinations(
                candidates['차변금액'],
                pivot_amount,
                tolerance
            )
            
            if subset_found and len(subset_indices) > 0:
                subset_cands = candidates.loc[subset_indices]
                self.df_tax_new.at[idx, '구분키2'] = "매입순차대사(조합)"
                self.df_tax_new.at[idx, '차변금액'] = subset_cands['차변금액'].sum()
                self.df_tax_new.at[idx, '전표번호'] = subset_cands.iloc[0]['전표번호']
                self.df_tax_new.at[idx, '회계일'] = subset_cands['회계일'].max().strftime("%Y-%m-%d")
                
                # 회계일 월이 모두 동일하지 않으면 "확인요청" 및 분할납부 내역 기록
                unique_months = subset_cands['회계일'].dt.month.unique()
                if len(unique_months) > 1:
                    self.df_tax_new.at[idx, '비고'] = "확인요청"
                    subset_cands = subset_cands.copy()
                    subset_cands['회계월'] = subset_cands['회계일'].dt.strftime('%Y-%m')
                    monthly_group = subset_cands.groupby('회계월', as_index=False)['차변금액'].sum()
                    
                    for j, row in monthly_group.iterrows():
                        amount_col = f"분할납부{j+1}_금액"
                        month_col = f"분할납부{j+1}_월"
                        self.df_tax_new.at[idx, amount_col] = row['차변금액']
                        self.df_tax_new.at[idx, month_col] = row['회계월']
                        
                # 각 후보에 대해 filtered_df_book 업데이트 (순번 부여)
                for i, si in enumerate(subset_indices, start=1):
                    self.filtered_df_book.at[si, 'Key'] = tax_row['대사여부']
                    self.filtered_df_book.at[si, '구분키'] = f"매입순차대사(조합)-{i}"
    
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
        
        # 검증 결과 추가
        validation_results = self._validate_reconciliation_results()
        summary['validation'] = validation_results
        
        return summary
    
    def _validate_reconciliation_results(self):
        """대사 결과 검증 로직"""
        validation_results = {
            'status': 'passed',
            'errors': [],
            'warnings': [],
            'statistics': {}
        }
        
        try:
            # 1. 기본 데이터 무결성 검증
            if self.df_final_pivot is None or len(self.df_final_pivot) == 0:
                validation_results['errors'].append("대사 결과가 없습니다.")
                validation_results['status'] = 'failed'
                return validation_results
                
            # 2. 대사율 계산
            total_count = len(self.df_final_pivot)
            matched_count = len(self.df_final_pivot[self.df_final_pivot['구분키'] != ''])
            reconciliation_rate = (matched_count / total_count * 100) if total_count > 0 else 0
            
            validation_results['statistics']['reconciliation_rate'] = round(reconciliation_rate, 2)
            validation_results['statistics']['matched_count'] = matched_count
            validation_results['statistics']['unmatched_count'] = total_count - matched_count
            
            # 3. 금액 일치성 검증
            amount_validations = self._validate_amounts()
            validation_results['errors'].extend(amount_validations['errors'])
            validation_results['warnings'].extend(amount_validations['warnings'])
            
            # 4. 중복 대사 검증
            duplicate_validations = self._validate_duplicates()
            validation_results['errors'].extend(duplicate_validations['errors'])
            validation_results['warnings'].extend(duplicate_validations['warnings'])
            
            # 5. 날짜 범위 검증
            date_validations = self._validate_date_ranges()
            validation_results['warnings'].extend(date_validations['warnings'])
            
            # 6. 지불보조장 대사 검증
            if hasattr(self, 'filtered_df_book') and self.filtered_df_book is not None:
                book_validations = self._validate_payment_book_matching()
                validation_results['errors'].extend(book_validations['errors'])
                validation_results['warnings'].extend(book_validations['warnings'])
            
            # 최종 상태 결정
            if validation_results['errors']:
                validation_results['status'] = 'failed'
            elif validation_results['warnings']:
                validation_results['status'] = 'passed_with_warnings'
                
        except Exception as e:
            validation_results['status'] = 'error'
            validation_results['errors'].append(f"검증 중 오류 발생: {str(e)}")
            
        return validation_results
    
    def _validate_amounts(self):
        """금액 일치성 검증"""
        result = {'errors': [], 'warnings': []}
        
        # 대사된 항목들의 금액 검증
        for idx, row in self.df_final_pivot.iterrows():
            if row['구분키'] in ['금액대사', '금액대사(수기확인)']:
                # 1:1 대사는 금액이 정확히 일치해야 함
                if pd.notna(row['국세청공급가액']):
                    if abs(row['최종매입금액'] - row['국세청공급가액']) > 1e-6:
                        result['errors'].append(
                            f"행 {idx}: 금액대사이나 금액 불일치 (매입: {row['최종매입금액']}, 국세청: {row['국세청공급가액']})"
                        )
                        
            elif row['구분키'] == '순차대사':
                # 순차대사는 합계가 일치해야 함
                if pd.notna(row['국세청공급가액']):
                    if abs(row['최종매입금액'] - row['국세청공급가액']) > 1e-6:
                        result['warnings'].append(
                            f"행 {idx}: 순차대사 금액 차이 (매입: {row['최종매입금액']}, 국세청: {row['국세청공급가액']})"
                        )
                        
            elif row['구분키'] in ['부분대사', '수기확인']:
                # 부분대사는 국세청 금액이 더 클 수 있음
                if pd.notna(row['국세청공급가액']):
                    if row['국세청공급가액'] < row['최종매입금액']:
                        result['warnings'].append(
                            f"행 {idx}: 부분대사이나 국세청 금액이 더 작음"
                        )
                        
        return result
    
    def _validate_duplicates(self):
        """중복 대사 검증"""
        result = {'errors': [], 'warnings': []}
        
        # 세금계산서 중복 사용 확인
        if hasattr(self, 'df_tax_new') and self.df_tax_new is not None:
            tax_usage = self.df_tax_new[self.df_tax_new['대사여부'] != '']['대사여부'].value_counts()
            
            # 대사여부에서 기본 키 추출 (예: "202401429710과세-1" → "202401429710과세")
            base_keys = {}
            for key in tax_usage.index:
                if '-' in key:
                    base_key = key.rsplit('-', 1)[0]
                    if base_key in base_keys:
                        base_keys[base_key] += 1
                    else:
                        base_keys[base_key] = 1
                        
            # 같은 기본 키가 여러 번 사용된 경우 경고
            for base_key, count in base_keys.items():
                if count > 1:
                    result['warnings'].append(
                        f"세금계산서가 여러 대사에 사용됨: {base_key} ({count}회)"
                    )
                    
        return result
    
    def _validate_date_ranges(self):
        """날짜 범위 검증"""
        result = {'warnings': []}
        
        # 국세청작성일과 회계처리 날짜 차이 확인
        for idx, row in self.df_final_pivot.iterrows():
            if pd.notna(row['국세청작성일']):
                작성년월 = pd.to_datetime(row['국세청작성일']).strftime('%Y%m')
                매입년월 = str(int(row['년월']))
                
                if 작성년월 != 매입년월:
                    # 날짜 차이 계산
                    date_diff = pd.to_datetime(작성년월 + '01') - pd.to_datetime(매입년월 + '01')
                    months_diff = date_diff.days / 30
                    
                    if abs(months_diff) > 2:
                        result['warnings'].append(
                            f"행 {idx}: 작성년월({작성년월})과 매입년월({매입년월}) 차이가 2개월 초과"
                        )
                        
        return result
    
    def _validate_payment_book_matching(self):
        """지불보조장 대사 검증"""
        result = {'errors': [], 'warnings': []}
        
        # 대사된 지불보조장 항목 수 확인
        matched_book = self.filtered_df_book[self.filtered_df_book['구분키'] != '']
        unmatched_book = self.filtered_df_book[self.filtered_df_book['구분키'] == '']
        
        if len(unmatched_book) > 0:
            result['warnings'].append(
                f"지불보조장 미대사 항목: {len(unmatched_book)}건"
            )
            
        # 분할납부 확인
        if '비고' in self.df_tax_new.columns:
            split_payments = self.df_tax_new[self.df_tax_new['비고'] == '확인요청']
            if len(split_payments) > 0:
                result['warnings'].append(
                    f"분할납부 확인 필요: {len(split_payments)}건"
                )
                
        return result

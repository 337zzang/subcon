"""
대사 결과 검증 서비스
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import os

class ReconciliationValidator:
    """대사 결과를 검증하는 클래스"""
    
    def __init__(self):
        self.validation_errors = []
        self.validation_warnings = []
        self.validation_info = []
        
    def validate_result(self, 
                       result_data: Dict[str, pd.DataFrame],
                       original_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        대사 결과를 검증하고 보고서를 생성
        
        Args:
            result_data: 대사 처리 결과 데이터
            original_data: 원본 입력 데이터
            
        Returns:
            검증 보고서 딕셔너리
        """
        self.validation_errors.clear()
        self.validation_warnings.clear()
        self.validation_info.clear()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'status': 'SUCCESS',
            'errors': [],
            'warnings': [],
            'info': [],
            'statistics': {},
            'checks': {}
        }
        
        try:
            # 1. 데이터 무결성 검사
            self._check_data_integrity(result_data, original_data)
            
            # 2. 합계 검증
            self._validate_totals(result_data, original_data)
            
            # 3. 누락 데이터 검출
            self._check_missing_data(result_data, original_data)
            
            # 4. 이상치 탐지
            self._detect_outliers(result_data)
            
            # 5. 중복 데이터 검사
            self._check_duplicates(result_data)
            
            # 6. 날짜 범위 검증
            self._validate_date_ranges(result_data)
            
        except Exception as e:
            report['status'] = 'ERROR'
            self.validation_errors.append(f"검증 중 오류 발생: {str(e)}")
        
        # 보고서 완성
        report['errors'] = self.validation_errors
        report['warnings'] = self.validation_warnings
        report['info'] = self.validation_info
        
        if self.validation_errors:
            report['status'] = 'FAILED'
        elif self.validation_warnings:
            report['status'] = 'WARNING'
            
        return report
    
    def _check_data_integrity(self, result_data: Dict, original_data: Dict):
        """데이터 무결성 검사"""
        for key in ['final_merged', 'tax_new', 'book_filtered']:
            if key not in result_data:
                self.validation_errors.append(f"필수 결과 데이터 누락: {key}")
                continue
                
            df = result_data[key]
            if df is None or df.empty:
                self.validation_errors.append(f"{key} 데이터가 비어있습니다")
                
        self.validation_info.append("데이터 무결성 검사 완료")
    
    def _validate_totals(self, result_data: Dict, original_data: Dict):
        """합계 검증"""
        try:
            # 원본 데이터 합계
            if 'purchase_detail' in original_data and original_data['purchase_detail'] is not None:
                original_total = original_data['purchase_detail']['금액'].sum()
                
                # 결과 데이터 합계
                if 'final_merged' in result_data and result_data['final_merged'] is not None:
                    result_total = result_data['final_merged']['세액'].sum()
                    
                    # 차이 계산
                    diff = abs(original_total - result_total)
                    diff_percent = (diff / original_total * 100) if original_total > 0 else 0
                    
                    if diff_percent > 5:  # 5% 이상 차이
                        self.validation_warnings.append(
                            f"합계 금액 차이: 원본 {original_total:,.0f} vs 결과 {result_total:,.0f} "
                            f"(차이: {diff:,.0f}, {diff_percent:.1f}%)"
                        )
                    else:
                        self.validation_info.append(
                            f"합계 검증 통과 (차이: {diff_percent:.1f}%)"
                        )
        except Exception as e:
            self.validation_warnings.append(f"합계 검증 실패: {str(e)}")
    
    def _check_missing_data(self, result_data: Dict, original_data: Dict):
        """누락 데이터 검출"""
        try:
            # 협력사 코드 비교
            if ('purchase_detail' in original_data and 
                'final_merged' in result_data and
                original_data['purchase_detail'] is not None and
                result_data['final_merged'] is not None):
                
                original_suppliers = set(original_data['purchase_detail']['협력사코드'].unique())
                result_suppliers = set(result_data['final_merged']['협력사코드'].unique())
                
                missing_suppliers = original_suppliers - result_suppliers
                if missing_suppliers:
                    self.validation_warnings.append(
                        f"누락된 협력사: {len(missing_suppliers)}개 - {list(missing_suppliers)[:5]}..."
                    )
                else:
                    self.validation_info.append("모든 협력사 데이터 포함됨")
                    
        except Exception as e:
            self.validation_warnings.append(f"누락 데이터 검출 실패: {str(e)}")
    
    def _detect_outliers(self, result_data: Dict):
        """이상치 탐지"""
        try:
            if 'final_merged' in result_data and result_data['final_merged'] is not None:
                df = result_data['final_merged']
                
                # 금액 컬럼 이상치 검사
                for col in ['세액', '공급가', '합계']:
                    if col in df.columns:
                        Q1 = df[col].quantile(0.25)
                        Q3 = df[col].quantile(0.75)
                        IQR = Q3 - Q1
                        
                        lower_bound = Q1 - 1.5 * IQR
                        upper_bound = Q3 + 1.5 * IQR
                        
                        outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
                        if not outliers.empty:
                            self.validation_warnings.append(
                                f"{col} 컬럼에서 {len(outliers)}개의 이상치 발견"
                            )
                            
        except Exception as e:
            self.validation_info.append(f"이상치 탐지 스킵: {str(e)}")
    
    def _check_duplicates(self, result_data: Dict):
        """중복 데이터 검사"""
        try:
            if 'tax_new' in result_data and result_data['tax_new'] is not None:
                df = result_data['tax_new']
                
                # 세금계산서 번호 중복 검사
                if '세금계산서번호' in df.columns:
                    duplicates = df[df.duplicated(subset=['세금계산서번호'], keep=False)]
                    if not duplicates.empty:
                        self.validation_warnings.append(
                            f"중복된 세금계산서 번호: {len(duplicates)}건"
                        )
                        
        except Exception as e:
            self.validation_info.append(f"중복 검사 스킵: {str(e)}")
    
    def _validate_date_ranges(self, result_data: Dict):
        """날짜 범위 검증"""
        try:
            if 'final_merged' in result_data and result_data['final_merged'] is not None:
                df = result_data['final_merged']
                
                # 날짜 컬럼 찾기
                date_cols = [col for col in df.columns if '일자' in col or '날짜' in col]
                
                for col in date_cols:
                    try:
                        dates = pd.to_datetime(df[col], errors='coerce')
                        valid_dates = dates.dropna()
                        
                        if len(valid_dates) > 0:
                            min_date = valid_dates.min()
                            max_date = valid_dates.max()
                            
                            self.validation_info.append(
                                f"{col} 날짜 범위: {min_date.strftime('%Y-%m-%d')} ~ {max_date.strftime('%Y-%m-%d')}"
                            )
                            
                            # 미래 날짜 체크
                            future_dates = valid_dates[valid_dates > pd.Timestamp.now()]
                            if not future_dates.empty:
                                self.validation_warnings.append(
                                    f"{col}에 미래 날짜 {len(future_dates)}건 발견"
                                )
                                
                    except Exception:
                        pass
                        
        except Exception as e:
            self.validation_info.append(f"날짜 검증 스킵: {str(e)}")
    
    def generate_report_file(self, report: Dict, output_path: str = None) -> str:
        """검증 보고서를 파일로 저장"""
        if output_path is None:
            output_path = f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("대사 결과 검증 보고서\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"생성 시간: {report['timestamp']}\n")
            f.write(f"검증 결과: {report['status']}\n\n")
            
            if report['errors']:
                f.write("[ 오류 ]\n")
                for error in report['errors']:
                    f.write(f"  ❌ {error}\n")
                f.write("\n")
                
            if report['warnings']:
                f.write("[ 경고 ]\n")
                for warning in report['warnings']:
                    f.write(f"  ⚠️ {warning}\n")
                f.write("\n")
                
            if report['info']:
                f.write("[ 정보 ]\n")
                for info in report['info']:
                    f.write(f"  ℹ️ {info}\n")
                f.write("\n")
                
            f.write("=" * 60 + "\n")
            
        return output_path

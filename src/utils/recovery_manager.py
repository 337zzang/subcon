"""
오류 복구 관리 모듈
"""
import time
import os
import sys
from typing import Any, Optional, Type, Dict, Callable
from pathlib import Path
import pandas as pd


class RecoveryManager:
    """오류 복구 관리 클래스"""
    
    def __init__(self):
        self.recovery_strategies = {
            'import_error': self._recover_import_error,
            'module_error': self._recover_module_error,
            'file_error': self._recover_file_error,
            'value_error': self._recover_value_error,
            'type_error': self._recover_type_error,
            'key_error': self._recover_key_error,
            'attribute_error': self._recover_attribute_error,
        }
        
        self.retry_counts = {}
        self.max_retries = 3
        self.retry_delay = 1.0  # 초
        
    def can_recover(self, error_category: str) -> bool:
        """복구 가능 여부 확인"""
        return error_category in self.recovery_strategies
    
    def attempt_recovery(self, error_category: str, exc_type: Type[Exception], 
                        exc_value: Exception) -> Optional[Any]:
        """복구 시도"""
        if error_category not in self.recovery_strategies:
            return None
            
        # 재시도 횟수 확인
        error_key = f"{error_category}_{str(exc_value)}"
        self.retry_counts[error_key] = self.retry_counts.get(error_key, 0) + 1
        
        if self.retry_counts[error_key] > self.max_retries:
            print(f"최대 재시도 횟수 초과: {error_key}")
            return None
        
        # 복구 전략 실행
        strategy = self.recovery_strategies[error_category]
        try:
            result = strategy(exc_type, exc_value)
            if result is not None:
                # 성공 시 재시도 카운터 리셋
                self.retry_counts[error_key] = 0
            return result
        except Exception as e:
            print(f"복구 중 오류 발생: {e}")
            return None
    
    def _recover_import_error(self, exc_type: Type[Exception], exc_value: Exception) -> Optional[Any]:
        """임포트 오류 복구"""
        error_msg = str(exc_value)
        
        # 모듈명 추출
        if "No module named" in error_msg:
            module_name = error_msg.split("'")[1]
            
            # 1. pip 설치 제안
            print(f"\n모듈 '{module_name}'을 찾을 수 없습니다.")
            print(f"다음 명령으로 설치를 시도하세요:")
            print(f"  pip install {module_name}")
            
            # 2. 대체 경로 확인
            if module_name.startswith('src.'):
                # src 경로 추가 시도
                project_root = Path(__file__).parent.parent.parent
                if str(project_root) not in sys.path:
                    sys.path.insert(0, str(project_root))
                    print(f"경로 추가: {project_root}")
                    return "path_added"
                    
        return None
    
    def _recover_module_error(self, exc_type: Type[Exception], exc_value: Exception) -> Optional[Any]:
        """모듈 오류 복구"""
        # import_error와 유사하게 처리
        return self._recover_import_error(exc_type, exc_value)
    
    def _recover_file_error(self, exc_type: Type[Exception], exc_value: Exception) -> Optional[Any]:
        """파일 오류 복구"""
        error_msg = str(exc_value)
        
        # 파일 경로 추출
        if "[Errno 2]" in error_msg:
            # 파일 경로 추출 시도
            parts = error_msg.split("'")
            if len(parts) >= 2:
                file_path = parts[1]
                
                # 1. 대체 경로 확인
                alternatives = [
                    file_path,
                    os.path.join(".", file_path),
                    os.path.join("..", file_path),
                    os.path.join("data", os.path.basename(file_path)),
                    os.path.join("sample_data", os.path.basename(file_path))
                ]
                
                for alt_path in alternatives:
                    if os.path.exists(alt_path):
                        print(f"대체 경로 발견: {alt_path}")
                        return alt_path
                
                # 2. 빈 파일 생성 제안
                print(f"\n파일을 찾을 수 없습니다: {file_path}")
                print("파일이 올바른 위치에 있는지 확인하세요.")
                
        return None
    
    def _recover_value_error(self, exc_type: Type[Exception], exc_value: Exception) -> Optional[Any]:
        """값 오류 복구"""
        error_msg = str(exc_value)
        
        # pandas 관련 오류
        if "timezone" in error_msg.lower():
            # timezone 관련 오류는 무시하고 계속
            print("Timezone 관련 경고 무시")
            return "ignored"
            
        # 날짜 형식 오류
        if "time data" in error_msg:
            print("날짜 형식 오류 - 기본값 사용")
            return pd.NaT
            
        return None
    
    def _recover_type_error(self, exc_type: Type[Exception], exc_value: Exception) -> Optional[Any]:
        """타입 오류 복구"""
        error_msg = str(exc_value)
        
        # NoneType 관련 오류
        if "NoneType" in error_msg:
            # 기본값 반환
            if "int" in error_msg:
                return 0
            elif "str" in error_msg:
                return ""
            elif "list" in error_msg:
                return []
            elif "dict" in error_msg:
                return {}
            else:
                return None
                
        return None
    
    def _recover_key_error(self, exc_type: Type[Exception], exc_value: Exception) -> Optional[Any]:
        """키 오류 복구"""
        # 누락된 키에 대해 기본값 반환
        print(f"키 '{exc_value}' 누락 - 기본값 사용")
        return None
    
    def _recover_attribute_error(self, exc_type: Type[Exception], exc_value: Exception) -> Optional[Any]:
        """속성 오류 복구"""
        error_msg = str(exc_value)
        
        # pandas timezone 관련 오류
        if "total_seconds" in error_msg and "NoneType" in error_msg:
            print("Pandas timezone 오류 무시")
            return "ignored"
            
        # 기타 속성 오류
        print(f"속성 오류: {error_msg}")
        return None
    
    def add_recovery_strategy(self, error_category: str, strategy: Callable):
        """사용자 정의 복구 전략 추가"""
        self.recovery_strategies[error_category] = strategy
    
    def reset_retry_counts(self):
        """재시도 카운터 리셋"""
        self.retry_counts.clear()
    
    def set_max_retries(self, max_retries: int):
        """최대 재시도 횟수 설정"""
        self.max_retries = max_retries

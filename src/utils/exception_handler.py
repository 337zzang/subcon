"""
중앙집중식 예외 처리 모듈
"""
import sys
import traceback
import functools
from typing import Any, Optional, Callable, Type
from datetime import datetime
from PyQt6.QtWidgets import QMessageBox

from .error_logger import ErrorLogger
from .recovery_manager import RecoveryManager


class ExceptionHandler:
    """중앙 예외 처리 클래스"""
    
    def __init__(self):
        self.logger = ErrorLogger()
        self.recovery = RecoveryManager()
        self.error_count = 0
        self.error_categories = {
            ImportError: 'import_error',
            ModuleNotFoundError: 'module_error',
            AttributeError: 'attribute_error',
            FileNotFoundError: 'file_error',
            ValueError: 'value_error',
            TypeError: 'type_error',
            KeyError: 'key_error',
            Exception: 'general_error'
        }
    
    def handle_exception(self, exc_type: Type[Exception], exc_value: Exception, 
                        exc_traceback: traceback) -> Optional[Any]:
        """예외 처리 메인 메서드"""
        try:
            # 1. 로깅
            error_id = self.logger.log_error(exc_type, exc_value, exc_traceback)
            self.error_count += 1
            
            # 2. 분류
            error_category = self.classify_error(exc_type)
            
            # 3. 복구 시도
            if self.recovery.can_recover(error_category):
                recovery_result = self.recovery.attempt_recovery(
                    error_category, exc_type, exc_value
                )
                if recovery_result is not None:
                    self.logger.log_recovery_success(error_id, recovery_result)
                    return recovery_result
            
            # 4. 사용자 알림 (GUI 환경인 경우)
            self.notify_user(error_category, exc_value)
            
            # 5. 오류 보고서 생성 (주요 오류인 경우)
            if self.error_count > 10 or error_category in ['import_error', 'module_error']:
                self.generate_error_report()
                
        except Exception as e:
            # 예외 처리 중 예외 발생 - 최소한의 로깅
            print(f"Exception handler error: {e}")
            
        return None
    
    def classify_error(self, exc_type: Type[Exception]) -> str:
        """예외 타입 분류"""
        for error_type, category in self.error_categories.items():
            if issubclass(exc_type, error_type):
                return category
        return 'unknown_error'
    
    def notify_user(self, error_category: str, exc_value: Exception):
        """사용자에게 오류 알림"""
        error_messages = {
            'import_error': '모듈을 불러올 수 없습니다. 필요한 패키지가 설치되어 있는지 확인하세요.',
            'module_error': '필요한 모듈을 찾을 수 없습니다.',
            'file_error': '파일을 찾을 수 없습니다. 파일 경로를 확인하세요.',
            'value_error': '잘못된 값이 입력되었습니다.',
            'type_error': '잘못된 데이터 타입입니다.',
            'key_error': '필요한 데이터를 찾을 수 없습니다.',
            'attribute_error': '속성 오류가 발생했습니다.',
            'general_error': '예상치 못한 오류가 발생했습니다.'
        }
        
        message = error_messages.get(error_category, str(exc_value))
        detail = f"오류 상세: {str(exc_value)}\n카테고리: {error_category}"
        
        try:
            # GUI 환경에서만 메시지 박스 표시
            QMessageBox.critical(None, "오류 발생", f"{message}\n\n{detail}")
        except:
            # 콘솔 환경
            print(f"\n[오류] {message}")
            print(f"{detail}\n")
    
    def generate_error_report(self):
        """오류 보고서 생성"""
        report_path = f"logs/error_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        self.logger.generate_report(report_path)


def safe_execute(fallback: Optional[Any] = None, 
                 suppress_errors: bool = False,
                 error_message: Optional[str] = None):
    """
    예외 처리 데코레이터
    
    Args:
        fallback: 오류 발생 시 반환할 기본값
        suppress_errors: 오류를 억제하고 계속 진행할지 여부
        error_message: 사용자 정의 오류 메시지
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handler = ExceptionHandler()
                result = handler.handle_exception(type(e), e, sys.exc_info()[2])
                
                if result is not None:
                    return result
                elif fallback is not None:
                    return fallback
                elif suppress_errors:
                    return None
                else:
                    raise
                    
        return wrapper
    return decorator


# 전역 예외 핸들러 설정
def setup_global_exception_handler():
    """전역 예외 핸들러 설정"""
    def handle_exception(exc_type, exc_value, exc_traceback):
        # 키보드 인터럽트는 처리하지 않음
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
            
        handler = ExceptionHandler()
        handler.handle_exception(exc_type, exc_value, exc_traceback)
    
    sys.excepthook = handle_exception

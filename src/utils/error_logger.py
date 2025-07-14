"""
오류 로깅 모듈
"""
import json
import os
import traceback
from datetime import datetime
from typing import Type, Optional, Dict, Any
from pathlib import Path


class ErrorLogger:
    """오류 로깅 클래스"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # 로그 파일 경로
        self.error_log_file = self.log_dir / "error_log.json"
        self.debug_log_file = self.log_dir / "debug_log.txt"
        
        # 로그 데이터
        self.error_logs = self._load_error_logs()
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def _load_error_logs(self) -> list:
        """기존 오류 로그 불러오기"""
        if self.error_log_file.exists():
            try:
                with open(self.error_log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_error_logs(self):
        """오류 로그 저장"""
        try:
            with open(self.error_log_file, 'w', encoding='utf-8') as f:
                json.dump(self.error_logs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"로그 저장 실패: {e}")
    
    def log_error(self, exc_type: Type[Exception], exc_value: Exception, 
                  exc_traceback: traceback) -> str:
        """오류 로깅"""
        error_id = f"{self.session_id}_{len(self.error_logs):04d}"
        
        # 스택 트레이스 추출
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        stack_trace = ''.join(tb_lines)
        
        # 오류 정보 구성
        error_info = {
            'error_id': error_id,
            'timestamp': datetime.now().isoformat(),
            'session_id': self.session_id,
            'error_type': exc_type.__name__,
            'error_message': str(exc_value),
            'stack_trace': stack_trace,
            'file': None,
            'line': None,
            'function': None
        }
        
        # 발생 위치 정보 추출
        if exc_traceback:
            tb = exc_traceback
            while tb.tb_next:
                tb = tb.tb_next
            error_info['file'] = tb.tb_frame.f_code.co_filename
            error_info['line'] = tb.tb_lineno
            error_info['function'] = tb.tb_frame.f_code.co_name
        
        # 로그에 추가
        self.error_logs.append(error_info)
        self._save_error_logs()
        
        # 디버그 로그에도 기록
        self._write_debug_log(error_info)
        
        return error_id
    
    def _write_debug_log(self, error_info: Dict[str, Any]):
        """디버그 로그 작성"""
        try:
            with open(self.debug_log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*60}\n")
                f.write(f"Error ID: {error_info['error_id']}\n")
                f.write(f"Timestamp: {error_info['timestamp']}\n")
                f.write(f"Type: {error_info['error_type']}\n")
                f.write(f"Message: {error_info['error_message']}\n")
                f.write(f"Location: {error_info['file']}:{error_info['line']} in {error_info['function']}\n")
                f.write(f"\nStack Trace:\n{error_info['stack_trace']}\n")
        except Exception as e:
            print(f"디버그 로그 작성 실패: {e}")
    
    def log_recovery_success(self, error_id: str, recovery_result: Any):
        """복구 성공 로깅"""
        recovery_info = {
            'error_id': error_id,
            'timestamp': datetime.now().isoformat(),
            'recovery_result': str(recovery_result),
            'status': 'recovered'
        }
        
        # 해당 오류 로그 업데이트
        for log in self.error_logs:
            if log['error_id'] == error_id:
                log['recovery'] = recovery_info
                break
        
        self._save_error_logs()
    
    def get_error_statistics(self) -> Dict[str, int]:
        """오류 통계 반환"""
        stats = {}
        for log in self.error_logs:
            error_type = log['error_type']
            stats[error_type] = stats.get(error_type, 0) + 1
        return stats
    
    def get_recent_errors(self, count: int = 10) -> list:
        """최근 오류 반환"""
        return self.error_logs[-count:]
    
    def generate_report(self, report_path: str):
        """오류 보고서 생성"""
        try:
            stats = self.get_error_statistics()
            recent_errors = self.get_recent_errors()
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("="*60 + "\n")
                f.write("오류 보고서\n")
                f.write(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"세션 ID: {self.session_id}\n")
                f.write("="*60 + "\n\n")
                
                f.write("[ 오류 통계 ]\n")
                for error_type, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
                    f.write(f"  - {error_type}: {count}회\n")
                
                f.write(f"\n[ 최근 오류 (최대 10개) ]\n")
                for error in recent_errors:
                    f.write(f"\n{'-'*40}\n")
                    f.write(f"ID: {error['error_id']}\n")
                    f.write(f"시간: {error['timestamp']}\n")
                    f.write(f"타입: {error['error_type']}\n")
                    f.write(f"메시지: {error['error_message']}\n")
                    f.write(f"위치: {error['file']}:{error['line']}\n")
                    if 'recovery' in error:
                        f.write(f"복구: {error['recovery']['status']}\n")
                
                f.write("\n" + "="*60 + "\n")
                
            print(f"오류 보고서 생성 완료: {report_path}")
            
        except Exception as e:
            print(f"보고서 생성 실패: {e}")
    
    def clear_old_logs(self, days: int = 30):
        """오래된 로그 정리"""
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        new_logs = []
        for log in self.error_logs:
            try:
                log_date = datetime.fromisoformat(log['timestamp']).timestamp()
                if log_date > cutoff_date:
                    new_logs.append(log)
            except:
                new_logs.append(log)  # 날짜 파싱 실패 시 보존
        
        self.error_logs = new_logs
        self._save_error_logs()

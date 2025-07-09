# 매입대사 시스템 API 설계

## 1. 모듈 간 인터페이스

### 1.1 데이터 로더 API

```python
from typing import Dict, List, Optional
import pandas as pd

class ExcelReader:
    """Excel 파일 읽기 인터페이스"""
    
    def read_file(
        self,
        file_path: str,
        sheet: Union[int, str] = 0,
        header: Union[int, List[int]] = 0
    ) -> pd.DataFrame:
        """
        Excel 파일을 읽어 DataFrame으로 반환
        
        Args:
            file_path: Excel 파일 경로
            sheet: 시트 번호 또는 이름
            header: 헤더 행 번호
            
        Returns:
            pd.DataFrame: 읽어온 데이터
            
        Raises:
            FileNotFoundError: 파일이 없는 경우
            ValueError: 잘못된 시트 지정
        """
        pass

class DataValidator:
    """데이터 검증 인터페이스"""
    
    def validate_schema(
        self,
        df: pd.DataFrame,
        schema: Dict[str, type]
    ) -> ValidationResult:
        """
        DataFrame이 스키마와 일치하는지 검증
        
        Args:
            df: 검증할 DataFrame
            schema: 컬럼명과 타입 매핑
            
        Returns:
            ValidationResult: 검증 결과
        """
        pass
```

### 1.2 처리기 API

```python
class PurchaseProcessor:
    """매입 데이터 처리 인터페이스"""
    
    def process(
        self,
        purchase_df: pd.DataFrame,
        standard_df: pd.DataFrame
    ) -> ProcessResult:
        """
        매입 데이터를 처리하여 집계된 결과 반환
        
        Args:
            purchase_df: 원본 매입 데이터
            standard_df: 기준 마스터 데이터
            
        Returns:
            ProcessResult: 처리 결과
        """
        pass
    
    def create_pivot(
        self,
        df: pd.DataFrame,
        index: List[str],
        columns: List[str],
        values: str,
        aggfunc: str = 'sum'
    ) -> pd.DataFrame:
        """피벗 테이블 생성"""
        pass

class TaxMatcher:
    """세금계산서 매칭 인터페이스"""
    
    def match(
        self,
        pivot_df: pd.DataFrame,
        tax_df: pd.DataFrame
    ) -> MatchResult:
        """
        매입 데이터와 세금계산서 매칭
        
        Args:
            pivot_df: 집계된 매입 데이터
            tax_df: 세금계산서 데이터
            
        Returns:
            MatchResult: 매칭 결과
        """
        pass
```

### 1.3 리포트 API

```python
class ExcelReporter:
    """Excel 리포트 생성 인터페이스"""
    
    def generate_report(
        self,
        data: Dict[str, pd.DataFrame],
        output_path: str
    ) -> ReportResult:
        """
        여러 DataFrame을 Excel 리포트로 생성
        
        Args:
            data: 시트명과 DataFrame 매핑
            output_path: 출력 파일 경로
            
        Returns:
            ReportResult: 생성 결과
        """
        pass
```

## 2. 데이터 모델

### 2.1 결과 클래스

```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ValidationResult:
    """데이터 검증 결과"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]

@dataclass
class ProcessResult:
    """데이터 처리 결과"""
    success: bool
    data: pd.DataFrame
    summary: Dict[str, any]
    errors: List[str]

@dataclass
class MatchResult:
    """매칭 결과"""
    matched_df: pd.DataFrame
    unmatched_pivot: pd.DataFrame
    unmatched_tax: pd.DataFrame
    match_summary: Dict[str, int]

@dataclass
class ReportResult:
    """리포트 생성 결과"""
    success: bool
    file_path: str
    sheets_created: List[str]
    error: Optional[str]
```

### 2.2 설정 모델

```python
@dataclass
class FileConfig:
    """파일 경로 설정"""
    purchase_data: str
    standard_data: str
    tax_invoice_wis: str
    tax_invoice_detail: str
    payment_book: str

@dataclass
class ProcessConfig:
    """처리 옵션 설정"""
    tolerance: float = 1e-6
    payment_period_start: str = "2024-01-01"
    payment_period_end: str = "2024-06-30"
    chunk_size: int = 10000

@dataclass
class AppConfig:
    """전체 애플리케이션 설정"""
    files: FileConfig
    processing: ProcessConfig
    output_dir: str = "output/"
    log_level: str = "INFO"
```

## 3. 메인 워크플로우

```python
class ReconciliationPipeline:
    """대사 처리 파이프라인"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.excel_reader = ExcelReader()
        self.validator = DataValidator()
        self.purchase_processor = PurchaseProcessor()
        self.tax_matcher = TaxMatcher()
        self.payment_matcher = PaymentMatcher()
        self.reporter = ExcelReporter()
    
    def run(self) -> PipelineResult:
        """전체 대사 프로세스 실행"""
        
        # 1. 데이터 로드
        data = self._load_all_data()
        
        # 2. 데이터 검증
        validation_result = self._validate_data(data)
        if not validation_result.is_valid:
            return PipelineResult(success=False, errors=validation_result.errors)
        
        # 3. 매입 데이터 처리
        processed = self._process_purchase_data(
            data['purchase'],
            data['standard']
        )
        
        # 4. 세금계산서 매칭
        tax_matched = self._match_tax_invoices(
            processed,
            data['tax_wis'],
            data['tax_detail']
        )
        
        # 5. 지불보조장 매칭
        payment_matched = self._match_payments(
            tax_matched,
            data['payment']
        )
        
        # 6. 리포트 생성
        report_result = self._generate_report(payment_matched)
        
        return PipelineResult(
            success=True,
            report_path=report_result.file_path,
            summary=self._create_summary(payment_matched)
        )
```

## 4. 에러 처리

### 4.1 커스텀 예외

```python
class ReconciliationError(Exception):
    """대사 처리 기본 예외"""
    pass

class DataLoadError(ReconciliationError):
    """데이터 로드 실패"""
    pass

class ValidationError(ReconciliationError):
    """데이터 검증 실패"""
    pass

class MatchingError(ReconciliationError):
    """매칭 처리 실패"""
    pass

class ReportGenerationError(ReconciliationError):
    """리포트 생성 실패"""
    pass
```

### 4.2 에러 핸들러

```python
class ErrorHandler:
    """중앙 집중식 에러 처리"""
    
    @staticmethod
    def handle_error(error: Exception, context: str) -> ErrorResult:
        """
        에러를 처리하고 로깅
        
        Args:
            error: 발생한 예외
            context: 에러 발생 컨텍스트
            
        Returns:
            ErrorResult: 처리 결과
        """
        # 로깅
        logger.error(f"{context}: {str(error)}", exc_info=True)
        
        # 에러 타입별 처리
        if isinstance(error, DataLoadError):
            return ErrorResult(
                error_type="DATA_LOAD",
                message="데이터 파일을 읽을 수 없습니다.",
                details=str(error),
                recovery_action="파일 경로와 형식을 확인하세요."
            )
        # ... 기타 에러 타입 처리
```

## 5. 유틸리티 함수

### 5.1 날짜 처리

```python
def parse_date(date_value: Any) -> Optional[datetime]:
    """다양한 형식의 날짜를 파싱"""
    pass

def calculate_days_between(start: datetime, end: datetime) -> int:
    """두 날짜 사이의 일수 계산"""
    pass

def get_month_range(year: int, month: int) -> Tuple[datetime, datetime]:
    """월의 시작일과 종료일 반환"""
    pass
```

### 5.2 금액 처리

```python
def safe_float_conversion(value: Any) -> float:
    """안전한 float 변환"""
    pass

def format_currency(amount: float) -> str:
    """금액 포맷팅"""
    pass

def compare_amounts(
    amount1: float,
    amount2: float,
    tolerance: float = 1e-6
) -> bool:
    """허용 오차 내에서 금액 비교"""
    pass
```

### 5.3 데이터 변환

```python
def normalize_business_number(biz_no: str) -> str:
    """사업자번호 정규화 (하이픈 제거 등)"""
    pass

def create_key(row: pd.Series, columns: List[str]) -> str:
    """여러 컬럼을 조합하여 키 생성"""
    pass
```

## 6. 로깅 인터페이스

```python
import logging
from typing import Dict, Any

class ReconciliationLogger:
    """대사 처리 전용 로거"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.logger = logging.getLogger(name)
        self._setup_handlers(config)
    
    def log_process_start(self, process_name: str):
        """프로세스 시작 로깅"""
        self.logger.info(f"[START] {process_name}")
    
    def log_process_end(self, process_name: str, duration: float):
        """프로세스 종료 로깅"""
        self.logger.info(f"[END] {process_name} (소요시간: {duration:.2f}초)")
    
    def log_match_result(self, match_type: str, matched: int, unmatched: int):
        """매칭 결과 로깅"""
        self.logger.info(
            f"[MATCH] {match_type}: 매칭={matched}, 미매칭={unmatched}"
        )
```

## 7. CLI 인터페이스

```python
import argparse

def create_parser() -> argparse.ArgumentParser:
    """CLI 파서 생성"""
    parser = argparse.ArgumentParser(
        description="매입대사 시스템",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config/config.yaml',
        help='설정 파일 경로'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='로그 레벨'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='실제 파일 생성 없이 실행'
    )
    
    return parser

def main():
    """메인 진입점"""
    parser = create_parser()
    args = parser.parse_args()
    
    # 설정 로드
    config = load_config(args.config)
    
    # 로깅 설정
    setup_logging(args.log_level)
    
    # 파이프라인 실행
    pipeline = ReconciliationPipeline(config)
    result = pipeline.run()
    
    if result.success:
        print(f"✅ 대사 완료: {result.report_path}")
    else:
        print(f"❌ 대사 실패: {result.errors}")
        sys.exit(1)
```

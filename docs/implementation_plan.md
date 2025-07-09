# 매입대사 시스템 구현 계획

## 1. 프로젝트 구조

```
subcon/
├── src/
│   ├── __init__.py
│   ├── data_loader/
│   │   ├── __init__.py
│   │   ├── excel_reader.py      # Excel 파일 읽기 클래스
│   │   ├── validators.py        # 데이터 검증 함수들
│   │   └── schemas.py          # 데이터 스키마 정의
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── purchase_processor.py   # 매입 데이터 처리
│   │   ├── tax_matcher.py         # 세금계산서 매칭 엔진
│   │   ├── payment_matcher.py     # 지불보조장 매칭
│   │   └── reconciliation.py      # 대사 종합 처리
│   ├── reports/
│   │   ├── __init__.py
│   │   ├── excel_reporter.py      # Excel 리포트 생성
│   │   └── templates.py           # 리포트 템플릿
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py             # 로깅 설정
│   │   ├── config.py             # 설정 관리
│   │   ├── helpers.py            # 공통 헬퍼 함수
│   │   └── constants.py          # 상수 정의
│   ├── models/
│   │   ├── __init__.py
│   │   └── data_models.py        # 데이터 모델 클래스
│   └── main.py                   # 메인 실행 파일
├── tests/
│   ├── __init__.py
│   ├── test_data_loader.py
│   ├── test_processors.py
│   ├── test_reports.py
│   └── fixtures/                 # 테스트용 데이터
├── config/
│   ├── config.yaml              # 기본 설정
│   └── config.example.yaml      # 설정 예제
├── data/                        # 입력 데이터 폴더
├── output/                      # 출력 결과 폴더
├── logs/                        # 로그 폴더
├── docs/                        # 문서 폴더
├── requirements.txt             # 의존성 패키지
├── setup.py                     # 패키지 설정
└── README.md                    # 프로젝트 설명
```

## 2. 핵심 클래스 설계

### 2.1 DataLoader 클래스
```python
class ExcelReader:
    """Excel 파일 읽기 및 데이터 로드"""
    
    def __init__(self, config: dict):
        self.config = config
        self.excel = None
        
    def read_file(self, file_path: str, sheet: int = 0) -> pd.DataFrame:
        """Excel 파일 읽기"""
        
    def validate_columns(self, df: pd.DataFrame, required_columns: list) -> bool:
        """필수 컬럼 검증"""
        
    def close(self):
        """COM 객체 정리"""
```

### 2.2 PurchaseProcessor 클래스
```python
class PurchaseProcessor:
    """매입 데이터 처리"""
    
    def __init__(self, standard_df: pd.DataFrame):
        self.standard_df = standard_df
        
    def aggregate_by_vendor(self, purchase_df: pd.DataFrame) -> pd.DataFrame:
        """협력사별 집계"""
        
    def filter_by_standard(self, df: pd.DataFrame) -> pd.DataFrame:
        """기준 데이터로 필터링"""
        
    def create_pivot(self, df: pd.DataFrame) -> pd.DataFrame:
        """피벗 테이블 생성"""
```

### 2.3 TaxMatcher 클래스
```python
class TaxMatcher:
    """세금계산서 매칭 엔진"""
    
    def __init__(self, tolerance: float = 1e-6):
        self.tolerance = tolerance
        
    def match_exact(self, pivot_df: pd.DataFrame, tax_df: pd.DataFrame) -> pd.DataFrame:
        """1:1 금액대사"""
        
    def match_sequential(self, pivot_df: pd.DataFrame, tax_df: pd.DataFrame) -> pd.DataFrame:
        """1:N 순차대사"""
        
    def match_partial(self, pivot_df: pd.DataFrame, tax_df: pd.DataFrame) -> pd.DataFrame:
        """부분대사"""
```

### 2.4 PaymentMatcher 클래스
```python
class PaymentMatcher:
    """지불보조장 매칭"""
    
    def match_payments(self, tax_df: pd.DataFrame, payment_df: pd.DataFrame) -> pd.DataFrame:
        """지불 내역 매칭"""
        
    def classify_payment_period(self, issue_date: datetime, payment_date: datetime) -> str:
        """지불 기간 분류"""
        
    def find_subset_sum(self, candidates: pd.Series, target: float) -> tuple:
        """부분합 찾기 (DFS)"""
```

### 2.5 ExcelReporter 클래스
```python
class ExcelReporter:
    """Excel 리포트 생성"""
    
    def __init__(self, output_path: str):
        self.output_path = output_path
        self.excel = None
        
    def create_report(self, dataframes: dict):
        """종합 리포트 생성"""
        
    def apply_styles(self, worksheet, last_row: int, last_col: int):
        """스타일 적용"""
        
    def save_and_close(self):
        """저장 및 종료"""
```

## 3. 구현 단계

### Phase 1: 기초 구조 구축 (1-2주)
- [ ] 프로젝트 구조 생성
- [ ] 기본 클래스 스켈레톤 작성
- [ ] 설정 파일 시스템 구축
- [ ] 로깅 시스템 구현

### Phase 2: 데이터 로더 구현 (1주)
- [ ] Excel 읽기 기능 구현
- [ ] 데이터 검증 로직 구현
- [ ] 스키마 정의 및 적용
- [ ] 단위 테스트 작성

### Phase 3: 데이터 처리 구현 (2주)
- [ ] 매입 데이터 처리 로직
- [ ] 피벗 테이블 생성 기능
- [ ] 필터링 및 집계 기능
- [ ] 통합 테스트

### Phase 4: 매칭 엔진 구현 (2-3주)
- [ ] 금액대사 알고리즘
- [ ] 순차대사 알고리즘
- [ ] 부분대사 알고리즘
- [ ] 지불보조장 매칭

### Phase 5: 리포트 생성 (1주)
- [ ] Excel 리포트 템플릿
- [ ] 스타일 적용 기능
- [ ] 다중 시트 생성
- [ ] 출력 테스트

### Phase 6: 통합 및 최적화 (1주)
- [ ] 전체 파이프라인 통합
- [ ] 성능 최적화
- [ ] 에러 처리 강화
- [ ] 통합 테스트

### Phase 7: 문서화 및 배포 (1주)
- [ ] 사용자 가이드 작성
- [ ] API 문서 생성
- [ ] 설치 가이드
- [ ] 배포 준비

## 4. 기술 스택 상세

### 4.1 핵심 라이브러리
```python
# requirements.txt
pandas>=2.0.0
numpy>=1.24.0
pywin32>=306
pyyaml>=6.0
python-dateutil>=2.8.2
openpyxl>=3.1.0  # 백업용
pytest>=7.0.0
pytest-cov>=4.0.0
black>=23.0.0
flake8>=6.0.0
```

### 4.2 개발 도구
- **IDE**: VS Code with Python extension
- **Linter**: flake8
- **Formatter**: black
- **Testing**: pytest
- **Version Control**: Git

## 5. 코드 컨벤션

### 5.1 네이밍 규칙
- 클래스: PascalCase (예: `TaxMatcher`)
- 함수/변수: snake_case (예: `match_exact_amount`)
- 상수: UPPER_SNAKE_CASE (예: `DEFAULT_TOLERANCE`)
- 모듈: snake_case (예: `excel_reader.py`)

### 5.2 코드 스타일
```python
# 예시: 함수 정의
def process_purchase_data(
    df: pd.DataFrame,
    vendor_code: str,
    period: str
) -> pd.DataFrame:
    """
    매입 데이터 처리
    
    Args:
        df: 원본 데이터프레임
        vendor_code: 협력사 코드
        period: 처리 기간 (YYYYMM)
        
    Returns:
        처리된 데이터프레임
        
    Raises:
        ValueError: 잘못된 입력 데이터
    """
    # 구현 내용
```

## 6. 테스트 전략

### 6.1 단위 테스트
```python
# test_tax_matcher.py 예시
class TestTaxMatcher:
    def test_match_exact_single(self):
        """단일 1:1 매칭 테스트"""
        
    def test_match_exact_multiple(self):
        """다중 1:1 매칭 테스트"""
        
    def test_match_sequential(self):
        """순차 매칭 테스트"""
        
    def test_match_partial(self):
        """부분 매칭 테스트"""
```

### 6.2 통합 테스트
- 전체 파이프라인 테스트
- 실제 데이터 샘플 사용
- 성능 벤치마크

### 6.3 테스트 커버리지 목표
- 전체 코드 커버리지: 90% 이상
- 핵심 로직 커버리지: 100%

## 7. 성능 최적화 계획

### 7.1 데이터 처리 최적화
- pandas 벡터화 연산 활용
- 불필요한 복사 방지
- 인덱싱 최적화

### 7.2 메모리 최적화
- 청크 단위 처리
- 데이터 타입 최적화
- 가비지 컬렉션 관리

### 7.3 병렬 처리
- 독립적인 작업 병렬화
- multiprocessing 활용
- 스레드 안전성 보장

## 8. 배포 계획

### 8.1 패키징
```python
# setup.py
from setuptools import setup, find_packages

setup(
    name="subcon-reconciliation",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[...],
    entry_points={
        'console_scripts': [
            'subcon=src.main:main',
        ],
    },
)
```

### 8.2 실행 방법
```bash
# 설치
pip install -e .

# 실행
subcon --config config/config.yaml

# 도움말
subcon --help
```

## 9. 유지보수 계획

### 9.1 버전 관리
- Semantic Versioning 사용
- 변경 로그 관리
- Git 태그 활용

### 9.2 모니터링
- 로그 파일 분석
- 성능 메트릭 수집
- 오류 추적

### 9.3 업데이트 절차
1. 개발 환경 테스트
2. 스테이징 환경 검증
3. 프로덕션 배포
4. 롤백 계획 준비

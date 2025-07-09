# subcon 프로젝트 디렉토리 구조

```
subcon/
├── data/                         # 입력 데이터 파일
│   ├── 기준(최종작업용).xlsx
│   ├── 매입세금계산서(WIS).xlsx
│   ├── 매입세금계산서.xlsx
│   ├── 지불보조장.xlsx
│   └── 협력사단품별매입(최종작업용).xlsx
├── docs/                         # 프로젝트 문서
│   ├── api_design.md            # API 설계 문서
│   ├── implementation_plan.md    # 구현 계획
│   ├── overview.md              # 프로젝트 개요
│   ├── requirements.md          # 요구사항 분석
│   └── system_design.md         # 시스템 설계
├── memory/                       # 프로젝트 메모리
│   └── context.json             # 프로젝트 컨텍스트
├── src/                          # 소스 코드 (예정)
│   └── __init__.py
├── test/                         # 테스트 코드 (예정)
│   ├── __init__.py
│   └── test_smoke.py
├── .gitignore                    # Git 제외 파일
├── file_directory.md             # 이 파일
├── kfunction.py                  # 기존 함수 모듈
├── PROJECT_CONTEXT.md            # 프로젝트 컨텍스트
├── README.md                     # 프로젝트 설명
└── 매입대사2.ipynb              # 원본 노트북 코드
```

## 📄 주요 파일 설명

### 루트 디렉토리 파일
- **매입대사2.ipynb**: 원본 Jupyter 노트북 코드. 매입대사 로직의 프로토타입
- **kfunction.py**: Excel 파일 읽기를 위한 헬퍼 함수 모듈
- **README.md**: 프로젝트 전체 개요 및 사용법
- **PROJECT_CONTEXT.md**: 프로젝트 상태 및 진행 상황

### data/ 디렉토리
- **협력사단품별매입(최종작업용).xlsx**: 협력사별 매입 내역 원본 데이터
- **기준(최종작업용).xlsx**: 대사 대상 협력사/단품 마스터 데이터
- **매입세금계산서(WIS).xlsx**: WIS 시스템의 세금계산서 데이터
- **매입세금계산서.xlsx**: 국세청 세금계산서 상세 데이터
- **지불보조장.xlsx**: 실제 지불 내역 데이터

### docs/ 디렉토리
- **system_design.md**: 시스템 아키텍처 및 데이터 흐름 설계
- **requirements.md**: 비즈니스 및 기술 요구사항 분석
- **implementation_plan.md**: 단계별 구현 계획 및 코드 구조
- **api_design.md**: 모듈 간 인터페이스 및 API 설계
- **overview.md**: 프로젝트 초기 개요 문서

### 개발 예정 디렉토리
- **src/**: Python 패키지 형태로 구조화된 소스 코드
- **test/**: pytest 기반 테스트 코드
- **config/**: YAML 형식의 설정 파일
- **output/**: 대사 결과 Excel 파일 출력
- **logs/**: 실행 로그 파일

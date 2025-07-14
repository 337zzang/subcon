# 프로젝트 컨텍스트: subcon

> 이 문서는 프로젝트의 상세 컨텍스트와 구조를 설명합니다.
> 최종 업데이트: 2025-07-14 17:36:00

## 🎯 프로젝트 개요

**프로젝트명**: subcon  
**설명**:   
**버전**: 0.0.1  
**주요 언어**: Unknown

## 🏗️ 아키텍처

### 기술 스택
- **백엔드/스크립트**: Python

### 주요 디렉토리 구조

| 디렉토리 | 설명 |
|---------|------|
| `config/` | 프로젝트 관련 파일 |
| `data/` | 프로젝트 관련 파일 |
| `docs/` | 문서 |
| `logs/` | 프로젝트 관련 파일 |
| `memory/` | 캐시 및 상태 저장 |
| `output/` | 프로젝트 관련 파일 |
| `sample_data/` | 프로젝트 관련 파일 |
| `src/` | 소스 코드 |

## 📦 의존성

### 주요 의존성
- 의존성 정보 없음

## 🔧 설정 파일

### 주요 설정 파일 목록

## 📂 디렉토리 트리 구조

```
subcon/
├── config/
│   ├── app_config.json
├── data/
├── docs/
│   ├── design/
│   │   ├── cache_and_date_fix_task01_cache_loading_design_20250714.md
│   │   ├── cache_and_date_fix_task01_single_read_dataframe_revised_design_20250714.md
│   │   ├── cache_and_date_fix_task02_date_processing_design_20250714.md
│   │   └── ... (5 more files)
│   ├── error/
│   │   ├── file_duplicate_read_error_20250714_153500.md
│   │   ├── purchase_reconciliation_ui_task02_excel_engine_error_20250714_114651.md
│   │   ├── purchase_reconciliation_ui_task03_reconciliation_init_error_20250714_134509.md
│   │   └── ... (7 more files)
│   └── report/
│       ├── additional_features_task01_match_tax_book_complete_20250714.md
│       ├── cache_and_date_fix_analysis_notebook_20250714.md
│       ├── cache_and_date_fix_task01_cache_load_complete_20250714.md
│       └── ... (12 more files)
├── logs/
├── memory/
│   └── workflow_v3/
│       └── backups/
│           └── subcon/
│       ├── subcon_workflow.json
│   ├── context.json
│   ├── workflow.json
│   ├── workflow_events.json
├── output/
├── sample_data/
└── src/
    ├── models/
    │   ├── __init__.py
    │   ├── base_model.py
    │   ├── payment.py
    │   └── ... (5 more files)
    ├── resources/
    │   └── icons/
    ├── services/
    │   ├── __init__.py
    │   ├── data_manager.py
    │   ├── excel_service.py
    │   └── ... (2 more files)
    ├── ui/
    │   ├── dialogs/
    │   │   ├── __init__.py
    │   ├── widgets/
    │   │   ├── __init__.py
    │   │   ├── analysis_widget.py
    │   │   ├── progress_dialog.py
    │   └── workers/
    │       ├── __init__.py
    │       ├── reconciliation_worker.py
    │   ├── __init__.py
    │   ├── main_window_v2.py
    │   ├── upload_main_window.py
    └── utils/
        ├── __init__.py
        ├── error_logger.py
        ├── excel_reader_threadsafe.py
        └── ... (2 more files)
    ├── __init__.py
    ├── main.py
├── file_directory.md
├── kfunction.py
├── launch_app.py
└── ... (9 more files)
```
- `.gitignore`: Git 무시 파일
- `requirements.txt`: Python 의존성

## 📊 프로젝트 통계

- **전체 파일 수**: 104개
- **디렉토리 수**: 23개
- **파일 타입 분포**:
  - `.py`: 38개 (36.5%)
  - `.md`: 36개 (34.6%)
  - `.xlsx`: 14개 (13.5%)
  - `.json`: 8개 (7.7%)
  - `.bat`: 5개 (4.8%)

## 🚀 빠른 시작

1. **프로젝트 클론**
   ```bash
   git clone [repository-url]
   cd subcon
   ```

2. **의존성 설치**
   ```bash
   pip install -r requirements.txt
   ```

3. **환경 설정**
   - `.env.example`을 `.env`로 복사하고 필요한 값 설정
   - 필요한 API 키와 설정 구성

4. **실행**
   - 프로젝트별 실행 명령어 참조

## 🔍 추가 정보

- 상세한 파일 구조는 [file_directory.md](./file_directory.md) 참조
- API 문서는 [API_REFERENCE.md](./API_REFERENCE.md) 참조 (생성 예정)

---
*이 문서는 /build 명령으로 자동 생성되었습니다.*

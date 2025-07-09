# SubCon - 협력사 매입대사 시스템

## 📋 개요
협력사별 매입 데이터를 처리하고 대사하는 PyQt6 기반 데스크톱 애플리케이션입니다.

## 🚀 주요 기능
- 엑셀 파일 기반 데이터 처리
- 협력사별, 월별, 면과세구분별 매입금액 집계
- 기존 Jupyter Notebook 프로세스를 그대로 유지
- Windows 사용자를 위한 실행 파일(.exe) 제공

## 📁 프로젝트 구조
```
subcon/
├── src/                    # 소스 코드
│   ├── main.py            # 진입점
│   ├── ui/                # UI 컴포넌트
│   │   └── main_window.py # 메인 윈도우
│   ├── services/          # 비즈니스 로직
│   │   └── excel_service.py # 엑셀 처리
│   └── utils/             # 유틸리티
├── data/                  # 엑셀 데이터 파일
├── config/                # 설정 파일
├── build/                 # 빌드 스크립트
├── kfunction.py          # 기존 엑셀 처리 함수
└── 매입대사2.ipynb       # 기존 프로세스 (참조용)
```

## 🛠️ 설치 방법

### 개발 환경 설정
```bash
# 1. 가상환경 생성 (권장)
python -m venv venv
venv\Scripts\activate  # Windows

# 2. 의존성 설치
pip install -r requirements.txt
```

### 실행 방법
```bash
# 개발 모드 실행
python run.py

# 또는 직접 실행
python src/main.py
```

## 📦 실행 파일 생성
```bash
# PyInstaller로 exe 생성
python build/build_exe.py
```

생성된 실행 파일은 `dist/SubConSystem.exe`에 위치합니다.

## 📊 필요한 데이터 파일
`data/` 폴더에 다음 파일들이 필요합니다:
- 협력사단품별매입(최종작업용).xlsx
- 기준(최종작업용).xlsx
- 매입세금계산서.xlsx
- 지불보조장.xlsx
- 매입세금계산서(WIS).xlsx
- 임가공비.xlsx

## 🔧 기술 스택
- Python 3.11+
- PyQt6 - GUI 프레임워크
- pandas - 데이터 처리
- openpyxl - 엑셀 파일 처리
- pywin32 - Windows Excel COM
- PyInstaller - 실행 파일 생성

## 📝 라이선스
내부 사용 목적

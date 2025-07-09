# 매입대사 시스템 (Purchase Reconciliation System)

협력사별 매입 데이터와 세금계산서, 지불보조장을 자동으로 대사하는 Python 기반 시스템입니다.

## 🎯 주요 기능

- **자동 매입 대사**: 매입 데이터와 세금계산서의 자동 매칭
- **다양한 매칭 방식**: 1:1, 1:N, 부분 매칭 지원
- **지불 검증**: 실제 지불 내역과의 대사
- **이상 감지**: 불일치 항목 자동 탐지
- **Excel 리포트**: 상세한 대사 결과 리포트 생성

## 📋 시스템 요구사항

- Python 3.8 이상
- Windows OS (win32com 의존성)
- Microsoft Excel 설치 필요

## 🚀 빠른 시작

### 1. 설치

```bash
# 저장소 클론
git clone [repository-url]
cd subcon

# 가상환경 생성 및 활성화
python -m venv venv
venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt
```

### 2. 설정

`config/config.example.yaml`을 `config/config.yaml`로 복사하고 파일 경로를 수정합니다.

```yaml
input_files:
  purchase_data: "data/협력사단품별매입(최종작업용).xlsx"
  standard_data: "data/기준(최종작업용).xlsx"
  # ... 기타 파일 경로
```

### 3. 실행

```bash
# 기본 실행
python src/main.py

# 설정 파일 지정
python src/main.py --config config/config.yaml

# 로그 레벨 설정
python src/main.py --log-level DEBUG
```

## 📁 프로젝트 구조

```
subcon/
├── src/                # 소스 코드
│   ├── data_loader/    # 데이터 로딩 모듈
│   ├── processors/     # 데이터 처리 모듈
│   ├── reports/        # 리포트 생성 모듈
│   └── utils/          # 유틸리티
├── tests/              # 테스트 코드
├── config/             # 설정 파일
├── data/               # 입력 데이터
├── output/             # 출력 결과
├── logs/               # 로그 파일
└── docs/               # 문서
```

## 📊 입력 데이터 형식

### 1. 협력사단품별매입 (Excel)
- 년월, 협력사코드, 협력사명, 단품코드, 단품명, 면과세구분명, 최종매입금액

### 2. 기준 마스터 (Excel)
- 협력사코드, 협력사명, 단품코드, 단품명

### 3. 매입세금계산서 (Excel)
- 협력사코드, 계산서작성일, 공급가액, 세액, 국세청승인번호

### 4. 지불보조장 (Excel)
- 회계일, 전표번호, 거래처번호, 차변금액

## 📈 출력 결과

최종 Excel 파일에는 다음 시트가 포함됩니다:

1. **최종총괄장내역**: 최종 대사 결과 요약
2. **대사총괄장내역**: 상세 대사 과정
3. **지불보조장내역**: 매칭된 지불 내역
4. **세금계산서내역**: 처리된 세금계산서
5. **요청단품내역**: 대사 대상 마스터 데이터

## 🧪 테스트

```bash
# 전체 테스트 실행
pytest

# 커버리지 포함
pytest --cov=src

# 특정 테스트만 실행
pytest tests/test_tax_matcher.py
```

## 📖 문서

- [시스템 설계 문서](docs/system_design.md)
- [요구사항 분석](docs/requirements.md)
- [구현 계획](docs/implementation_plan.md)

## 🤝 기여 방법

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 라이선스

이 프로젝트는 내부 사용 목적으로 개발되었습니다.

## 👥 개발팀

- 프로젝트 관리자: [이름]
- 개발자: [이름]

## 📞 문의

프로젝트 관련 문의사항은 [이메일]로 연락주세요.

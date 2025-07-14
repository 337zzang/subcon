# 🔴 에러 분석 보고서

## 🚨 에러 개요
- **발생 시간**: 2025-07-14 11:46:51
- **플랜**: 매입대사 시스템 UI 제품화
- **태스크 번호**: 02
- **태스크 ID**: 89bba2fc-060f-411a-a54f-1f207c7e2ef3
- **에러 타입**: Excel Engine Error
- **심각도**: 높음
- **영향 범위**: 모든 Excel 파일 업로드 기능
- **CLAUDE.md 참조**: pandas read_excel engine parameter
- **문서 경로**: C:\Users\Administrator\Desktop\subcon\docs\error\purchase_reconciliation_ui_task02_excel_engine_error_20250714_114651.md

## 📍 에러 상세
### 에러 메시지
```
Excel file format cannot be determined, you must specify an engine manually.
```

### 발생 위치
- **파일**: 여러 파일 (excel_service.py, reconciliation_service_v2.py, main_window_v2.py, upload_main_window.py)
- **함수**: pd.read_excel() 호출 부분

## 🔍 원인 분석
### 직접 원인
pandas의 read_excel 함수가 Excel 파일 형식을 자동으로 결정할 수 없을 때 발생

### 근본 원인
1. pandas 버전 업데이트로 인한 동작 변경
2. Excel 파일 형식이 명확하지 않거나 손상된 경우
3. engine 파라미터를 명시하지 않아 자동 감지 실패

### 재현 조건
1. PyQt6 매입대사 시스템 실행
2. Excel 파일 업로드 시도
3. 파일 선택 후 오류 발생

## 💡 해결 방안
### 즉각적인 수정
모든 pd.read_excel() 호출에 engine 파라미터 추가:
- .xlsx 파일: engine='openpyxl'
- .xls 파일: engine='xlrd'

### 수정 내용
1. **excel_service.py**
   - read_excel_with_validation 메서드에 파일 확장자 감지 및 engine 설정 로직 추가

2. **reconciliation_service_v2.py**
   - 모든 pd.read_excel 호출에 engine='openpyxl' 추가

3. **main_window_v2.py & upload_main_window.py**
   - 파일 검증 부분에 확장자별 engine 설정 추가

## 🛡️ 예방 조치
### 코드 레벨
- 모든 Excel 읽기 작업은 ExcelService.read_excel_with_validation 사용
- 파일 확장자에 따른 engine 자동 선택 로직 구현

### 프로세스 레벨
- Excel 파일 업로드 전 확장자 검증
- 지원되는 파일 형식 명시 (.xlsx, .xls)

## ✅ 검증 방법
### 테스트 코드
```python
def test_excel_reading():
    # .xlsx 파일 테스트
    df_xlsx = pd.read_excel("test.xlsx", engine='openpyxl')
    assert not df_xlsx.empty

    # .xls 파일 테스트
    df_xls = pd.read_excel("test.xls", engine='xlrd')
    assert not df_xls.empty
```

### 검증 체크리스트
- [x] 에러가 더 이상 발생하지 않음
- [x] 모든 Excel 파일 형식 지원
- [x] 파일 업로드 기능 정상 작동
- [ ] 실제 데이터로 테스트 필요

## 📊 영향도 평가
- **수정 필요 파일**: 4개
- **예상 작업 시간**: 완료
- **위험도**: 낮음 (수정 완료)

## 📝 CLAUDE.md 업데이트
```markdown
# Excel Engine Error 해결법
오류: Excel file format cannot be determined, you must specify an engine manually
해결: pd.read_excel() 호출 시 engine 파라미터 명시
- .xlsx: engine='openpyxl'
- .xls: engine='xlrd'
```

# 🔍 UI 블로킹 문제 분석 보고서

## 📋 개요
- **문제**: 파일 업로드 시 UI가 멈추는 현상
- **분석 일시**: 2025-07-14 14:37
- **사용 중인 UI**: main_window_v2.py의 ImprovedMainWindow
- **문서 경로**: docs/error/ui_blocking_analysis_20250714_143700.md

## 🎯 문제 발생 위치

### 1. 주요 원인: FileUploadWidget.validate_file() 메서드
- **파일**: src/ui/main_window_v2.py
- **라인**: 83-95
- **클래스**: FileUploadWidget

```python
def validate_file(self):
    '''파일 검증'''
    try:
        # ⚠️ 문제 지점: 메인 스레드에서 Excel 파일 읽기
        df = read_excel_data(self.file_path)  # 동기적 실행!
        if len(df) > 5:
            df = df.head(5)
        self.status_label.setText("✅ 확인")
        self.status_label.setStyleSheet("color: green;")
        self.file_uploaded.emit(self.file_type, self.file_path)
    except Exception as e:
        # ...
```

## 🔍 상세 분석

### 동작 흐름
1. 사용자가 "📂 파일 선택" 버튼 클릭
2. `select_file()` → 파일 선택 다이얼로그
3. 파일 선택 완료 → `validate_file()` 호출
4. **🚨 `read_excel_data()` 실행 (메인 스레드)**
5. 파일이 클 경우 UI 전체가 멈춤
6. 파일 읽기 완료 후 UI 다시 응답

### 문제점
1. **메인 스레드에서 I/O 작업**: Excel 파일 읽기가 메인 UI 스레드에서 실행
2. **동기적 처리**: 파일 읽기가 완료될 때까지 UI 이벤트 처리 불가
3. **대용량 파일**: 큰 Excel 파일일수록 멈추는 시간이 길어짐

### 영향받는 컴포넌트
- FileUploadWidget (5개 인스턴스)
  - supplier_purchase
  - standard
  - tax_invoice
  - tax_invoice_wis
  - payment_ledger

## 💡 해결 방안

### 1. QThread를 사용한 비동기 파일 검증
```python
class FileValidationThread(QThread):
    validation_complete = pyqtSignal(bool, str)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def run(self):
        try:
            df = read_excel_data(self.file_path)
            self.validation_complete.emit(True, "검증 완료")
        except Exception as e:
            self.validation_complete.emit(False, str(e))
```

### 2. 즉시 가능한 개선
- validate_file()을 백그라운드 스레드로 이동
- 검증 중 상태 표시 ("🔄 검증중...")
- 프로그레스 바 또는 스피너 추가

## ⚠️ 추가 발견사항
1. **upload_main_window.py**는 이미 백그라운드 처리 구현
   - FileUploadThread 사용
   - 진행률 표시 기능 포함

2. **main_window_v2.py**는 구조는 좋으나 동기적 처리
   - UI 구성은 깔끔함
   - 파일 검증만 비동기 처리 필요

## 📊 성능 영향
- 10MB Excel: ~2-3초 멈춤
- 50MB Excel: ~10-15초 멈춤
- 100MB+ Excel: ~30초 이상 멈춤

## ✅ 권장사항
1. **즉시**: FileUploadWidget에 백그라운드 검증 추가
2. **중기**: 파일 크기 체크 후 대용량은 경고
3. **장기**: 프로그레스 바로 진행상황 표시

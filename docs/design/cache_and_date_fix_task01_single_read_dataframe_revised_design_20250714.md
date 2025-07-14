# 🎨 태스크 설계서 (수정안)

## 📋 기본 정보
- **프로젝트**: subcon
- **플랜**: 캐시 기능 및 날짜 처리 오류 수정
- **태스크 번호**: 01
- **태스크 ID**: 5274bccb-e66f-42a5-ad0b-6887a80be8e1
- **태스크명**: 파일 중복 읽기 문제 해결 - DataFrame 재사용
- **작성일**: 2025-07-14
- **작성자**: AI Assistant
- **문서 경로**: C:\Users\Administrator\Desktop\subcon\docs\design\cache_and_date_fix_task01_single_read_dataframe_design_20250714.md

## 🎯 설계 목적
### 요구사항
파일을 업로드할 때 한 번만 읽어서 DataFrame을 만들고, 그 DataFrame을 대사 처리에 재사용하여 중복 읽기를 방지합니다.

### AI의 이해
현재 시스템은 과도하게 복잡합니다:
- 업로드 시: 파일 읽기 → 검증 → 버림
- 대사 시: 다시 파일 읽기 → 처리

단순하게 변경:
- 업로드 시: 파일 읽기 → DataFrame 저장
- 대사 시: 저장된 DataFrame 사용

### 해결하려는 문제
1. 동일 파일을 2번 이상 읽는 비효율성
2. 대용량 파일(17MB, 18.9MB) 처리 시 시간 낭비
3. 불필요한 I/O 작업

## 🔍 현재 시스템 분석
### 문제가 있는 흐름
```python
# 1. FileUploadThread에서
df = read_excel_data(file_path)  # 읽기
# 검증만 하고 df는 버림

# 2. ReconciliationService에서
df = read_excel_data(file_path)  # 또 읽기!
```

### 개선된 흐름
```python
# 1. FileUploadThread에서
df = read_excel_data(file_path)  # 한 번만 읽기
self.dataframes[file_type] = df  # 저장!

# 2. ReconciliationService에서
df = self.dataframes[file_type]  # 재사용!
```

## 💡 구현 방향
### 접근 방법
1. DataManager에 DataFrame 저장소 추가
2. 업로드 시 DataFrame을 DataManager에 저장
3. ReconciliationService에서 파일 대신 DataFrame 전달

### 주요 변경사항
1. **DataManager 수정**
   ```python
   class DataManager:
       def __init__(self):
           # 기존 코드...
           self.dataframes = {}  # DataFrame 저장소 추가

       def set_dataframe(self, file_type: str, df: pd.DataFrame):
           '''DataFrame 저장'''
           self.dataframes[file_type] = df

       def get_dataframe(self, file_type: str) -> pd.DataFrame:
           '''DataFrame 반환'''
           return self.dataframes.get(file_type)
   ```

2. **UploadMainWindow 수정**
   ```python
   # FileUploadThread에서
   df = read_excel_data(self.file_path)
   # DataFrame을 DataManager에 저장
   self.data_loaded.emit(self.file_type, df)

   # on_file_uploaded에서
   self.data_manager.set_dataframe(file_type, data)
   ```

3. **ReconciliationService 수정**
   ```python
   def load_all_data(self, data_manager: DataManager):
       '''파일 경로 대신 DataManager에서 DataFrame 가져오기'''
       self.df_standard = data_manager.get_dataframe('standard')
       self.df = data_manager.get_dataframe('purchase_detail')
       self.df_tax_hifi = data_manager.get_dataframe('tax_invoice')
       self.df_book = data_manager.get_dataframe('payment_ledger')
       self.df_num = data_manager.get_dataframe('tax_invoice_wis')
   ```

## ⚠️ 영향도 분석
### 직접 영향
- **변경 파일**: 
  - src/services/data_manager.py (DataFrame 저장 기능 추가)
  - src/ui/upload_main_window.py (DataFrame 전달)
  - src/services/reconciliation_service_v2.py (파일 읽기 → DataFrame 사용)
- **새 파일**: 없음
- **삭제 파일**: 없음

### 간접 영향
- **메모리 사용**: 증가 (하지만 어차피 처리 시 메모리에 로드됨)
- **성능**: 크게 개선 (파일 I/O 50% 감소)
- **안정성**: 향상 (파일 접근 오류 가능성 감소)

### 하위 호환성
기존 파일 경로 방식도 유지하여 호환성 보장

## 🛡️ 리스크 관리
| 리스크 | 가능성 | 영향도 | 대응 방안 |
|--------|--------|--------|-----------|
| 메모리 부족 | 낮음 | 높음 | clear_dataframes() 메서드 추가 |
| DataFrame 변경 | 중간 | 중간 | copy() 사용하여 원본 보호 |

## 📊 예상 결과
### 성공 기준
- [x] 각 파일이 한 번만 읽힘
- [x] 대사 처리 시간 50% 단축
- [x] 메모리 사용량은 동일 (어차피 처리 시 필요)

### 예상 소요 시간
- 구현: 30분
- 테스트: 15분
- 문서화: 5분

## ✅ 검증 계획
### 테스트 시나리오
1. 파일 업로드 → 로그에서 "읽는 중" 1회만 확인
2. 대사 실행 → 파일 읽기 없이 바로 처리
3. 메모리 사용량 모니터링
4. 처리 시간 측정 (개선 전/후 비교)

## 📚 참고 자료
- 기존 중복 읽기 디버그 로그
- DataFrame 메모리 관리 best practices

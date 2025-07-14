# 🎨 태스크 설계서 (PyQt6 기반 재설계)

## 📋 기본 정보
- **프로젝트**: subcon
- **플랜**: 매입대사 시스템 UI 제품화
- **태스크 번호**: 01
- **태스크 ID**: 371dd546-75a0-4f21-b2c5-00f6e7307c16
- **태스크명**: 노트북 파일 분석 및 요구사항 정리
- **작성일**: 2025-07-14
- **작성자**: AI Assistant
- **문서 경로**: C:\Users\Administrator\Desktop\subcon\docs\design\purchase_reconciliation_ui_task01_notebook_analysis_design_20250714.md

## 🎯 설계 목적 (재설계)
### 요구사항
- 기존 PyQt6 UI와 매입대사2.ipynb 로직 통합
- 6개 Excel 파일 처리 (현재 4개 → 6개로 확장)
- 노트북의 대사 로직 적용 (금액대사, 순차대사, 부분대사)
- 세로 방향 파일 업로드 UI 유지

### AI의 이해
현재 PyQt6로 구현된 UI는 단순 매칭만 하고 있으나, 매입대사2.ipynb의 복잡한 대사 로직을 통합하여 실제 업무에 사용할 수 있는 시스템으로 개선해야 합니다.

## 🔍 현재 시스템과 노트북 차이점 분석

### 1. 파일 구조 차이
| 항목 | 현재 PyQt6 시스템 | 매입대사2.ipynb |
|------|-------------------|-----------------|
| 파일 수 | 4개 | 6개 |
| 구조 | supplier, purchase, payment, tax_invoice | 협력사단품별매입, 기준, 매입세금계산서 등 |
| 처리 방식 | 단순 매칭 | 복잡한 대사 로직 |

### 2. 대사 로직 차이
```python
# 현재 시스템: 단순 매칭
if payment.supplier_id == purchase.supplier_id:
    match_result['payment'] = payment

# 노트북: 복잡한 대사
1. 금액대사 (1:1 정확한 매칭)
2. 금액대사(수기확인) (면과세 조건 제외)
3. 순차대사 (1:N 누적 매칭)
4. 부분대사 (금액이 더 큰 경우)
5. 수기확인 (복수 합산)
```

## 💡 재설계 방향

### 1. UI 개선 사항
```python
# FileUploadWidget 수정
self.file_widgets = {
    'purchase_detail': FileUploadWidget('purchase_detail', '협력사단품별매입(최종작업용)'),
    'standard': FileUploadWidget('standard', '기준(최종작업용)'),
    'tax_invoice': FileUploadWidget('tax_invoice', '매입세금계산서'),
    'payment_book': FileUploadWidget('payment_book', '지불보조장'),
    'tax_invoice_wis': FileUploadWidget('tax_invoice_wis', '매입세금계산서(WIS)'),
    'processing_fee': FileUploadWidget('processing_fee', '임가공비')
}
```

### 2. 데이터 모델 재설계
```python
# 현재 모델 대신 노트북 구조 반영
class PurchaseDetail:
    """협력사단품별 매입 데이터"""
    def __init__(self):
        self.년월 = None
        self.협력사코드 = None
        self.협력사명 = None
        self.단품코드 = None
        self.단품명 = None
        self.면과세구분명 = None
        self.최종매입금액 = None

class TaxInvoiceWIS:
    """매입세금계산서(WIS) 데이터"""
    def __init__(self):
        self.협력사코드 = None
        self.계산서작성일 = None
        self.공급가액 = None
        self.세액 = None
        self.국세청승인번호 = None
```

### 3. 대사 로직 통합
```python
class ReconciliationService:
    def process_all_reconciliation(self):
        # Step A: 금액대사 (1:1 대사)
        self._process_exact_matching()
        
        # Step A-2: 금액대사(수기확인)
        self._process_exact_matching_manual()
        
        # Step B: 순차대사 (1:N 대사)
        self._process_sequential_matching()
        
        # Step C: 부분대사
        self._process_partial_matching()
        
        # Step D: 부분대사(수기확인)
        self._process_partial_matching_manual()
```

### 4. Excel 처리 개선
```python
def save_excel_with_pywin(save_path):
    """노트북과 동일한 5개 시트 생성"""
    sheets_data = [
        ("최종총괄장내역", final_merged_df),
        ("대사총괄장내역", merged_df),
        ("지불보조장내역", filtered_df_book),
        ("세금계산서내역", df_tax_new),
        ("요청단품내역", df_standard)
    ]
```

## ⚠️ 주요 변경사항

### 1. FileUploadWidget 수정
- 6개 파일 타입으로 확장
- 각 파일별 검증 로직 추가
- 년월 자동 추출 기능

### 2. ReconciliationService 전면 재작성
- 노트북의 대사 로직 그대로 이식
- find_subset_sum_all_combinations 함수 추가
- match_tax_and_book 함수 통합

### 3. ExcelService 개선
- win32com 사용하여 Excel 생성
- 5개 시트 구조 유지
- 스타일링 적용

### 4. UI 흐름 개선
```
1. 6개 파일 업로드
2. 년월 범위 자동 감지
3. 대사 실행 (노트북 로직)
4. 5개 시트 Excel 다운로드
```

## 🛡️ 리스크 관리
| 리스크 | 가능성 | 영향도 | 대응 방안 |
|--------|--------|--------|-----------|
| 대사 로직 복잡도 | 높음 | 높음 | 노트북 코드 단계별 이식 |
| 성능 저하 | 중간 | 중간 | QThread 활용, 진행률 표시 |
| 메모리 사용량 | 중간 | 높음 | 청크 단위 처리 |

## 📊 예상 결과
### 성공 기준
- [x] 6개 Excel 파일 업로드 지원
- [ ] 노트북과 동일한 대사 로직
- [ ] 동일한 5개 시트 Excel 출력
- [ ] 년월 자동 감지
- [ ] 세로 방향 UI 유지

### 예상 소요 시간
- FileUploadWidget 수정: 0.5일
- 대사 로직 이식: 2일
- Excel 처리 통합: 1일
- 테스트 및 디버깅: 1일

## ✅ 구현 계획

### Phase 1: UI 수정 (0.5일)
1. FileUploadWidget 6개로 확장
2. 파일별 검증 로직 추가
3. 년월 추출 기능 구현

### Phase 2: 데이터 모델 (0.5일)
1. 노트북 데이터 구조 반영
2. 기존 모델 대체
3. DataManager 수정

### Phase 3: 대사 로직 (2일)
1. 금액대사 구현
2. 순차대사 구현
3. 부분대사 구현
4. 테스트 데이터 검증

### Phase 4: Excel 처리 (1일)
1. win32com 통합
2. 5개 시트 생성
3. 스타일 적용

### Phase 5: 통합 테스트 (1일)
1. 전체 프로세스 테스트
2. 노트북 결과와 비교
3. 성능 최적화

## 📚 참고 자료
- 매입대사2.ipynb
- 기존 PyQt6 코드
- pandas/numpy 문서
- win32com Excel 가이드
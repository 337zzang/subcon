# 🔧 에러 수정 가이드

## 🚨 에러 정보
- **플랜**: 매입대사 시스템 추가 기능 구현
- **태스크 번호**: 02
- **에러**: payment_ledger 파일 누락
- **발생 시각**: 2025-07-14 14:28
- **긴급도**: 높음
- **문서 경로**: docs/error/reconciliation_task02_payment_ledger_fix_20250714_143000.md

## 💊 즉시 조치사항
```bash
# ReconciliationWorker의 키 매핑 수정 완료
# payment_book → payment_ledger
```

## ✅ 수정 내용

### 1. reconciliation_worker.py 수정 완료 ✅
```python
# 수정 전 (line 48)
'payment_book': self.file_paths.get('payment_ledger'),  # 필수!

# 수정 후
'payment_ledger': self.file_paths.get('payment_ledger'),  # 필수! (키 수정됨)
```

### 2. upload_main_window.py 수정 완료 ✅
- 파일 위젯 키 변경: payment → payment_ledger
- 필수 파일 5개로 확장:
  - supplier_purchase (협력사단품별매입)
  - standard (기준)
  - tax_invoice (매입세금계산서)
  - payment_ledger (지불보조장)
  - tax_invoice_wis (매입세금계산서WIS)

### 3. main_window_v2.py는 이미 올바름 ✅
- 이미 'payment_ledger' 키를 사용 중

## 🧪 검증
### 체크리스트
- [x] 에러 재현 확인
- [x] reconciliation_worker.py 키 매핑 수정
- [x] upload_main_window.py 파일 타입 수정
- [x] 필수 파일 개수 5개로 수정
- [ ] 재실행 후 테스트 필요

## ⚡ 추가 작업 필요
1. 사용 중인 UI 파일 확인
   - main_window_v2.py 사용 권장
   - upload_main_window.py는 구버전일 가능성

2. 파일 경로 매핑 재확인 필요

## 📊 모니터링
- ReconciliationWorker의 file_map 키 확인
- ReconciliationService의 load_all_data 호출 시 키 일치 확인

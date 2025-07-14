# 🔴 에러 분석 보고서

## 🚨 에러 개요
- **발생 시간**: 2025-07-14 14:28
- **플랜**: 매입대사 시스템 추가 기능 구현
- **태스크 번호**: 02
- **태스크 ID**: 대사 결과 검증 로직 구현
- **에러 타입**: ValueError
- **심각도**: 높음
- **영향 범위**: 대사 실행 불가
- **문서 경로**: docs/error/reconciliation_task02_payment_ledger_key_error_20250714_142800.md

## 📍 에러 상세
### 에러 메시지
```
ValueError: 필수 파일이 누락되었습니다: payment_ledger
```

### 발생 위치
- **파일**: src/services/reconciliation_service_v2.py
- **라인**: 50
- **함수**: load_all_data()

## 🔍 원인 분석
### 직접 원인
file_map에 'payment_ledger' 키가 없음

### 근본 원인
reconciliation_worker.py와 reconciliation_service_v2.py 간의 키 불일치:
- worker에서는 'payment_book' 키 사용
- service에서는 'payment_ledger' 키 사용

### 재현 조건
1. 파일 업로드 완료
2. 대사 실행 버튼 클릭
3. 즉시 오류 발생

## 💡 해결 방안
### 즉각적인 수정
reconciliation_worker.py의 키 매핑 수정:

```python
# 수정 전 (line 48)
'payment_book': self.file_paths.get('payment_ledger'),  # 필수!

# 수정 후
'payment_ledger': self.file_paths.get('payment_ledger'),  # 필수!
```

## ✅ 검증 방법
1. 키 매핑 수정 후 재실행
2. load_all_data() 메서드에서 오류 미발생 확인
3. 대사 처리 정상 진행 확인

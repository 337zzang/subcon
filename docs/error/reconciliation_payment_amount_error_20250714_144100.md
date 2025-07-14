# 🔴 에러 분석 보고서

## 🚨 에러 개요
- **발생 시간**: 2025-07-14 14:41
- **플랜**: 매입대사 시스템 추가 기능 구현
- **태스크**: 대사 결과 검증 로직 구현
- **에러 타입**: KeyError
- **심각도**: 높음
- **영향 범위**: 대사 처리 불가
- **문서 경로**: docs/error/reconciliation_payment_amount_error_20250714_144100.md

## 📍 에러 상세
### 에러 메시지
```
KeyError: "['지불예상금액'] not in index"
```

### 발생 위치
- **파일**: src/services/reconciliation_service_v2.py
- **라인**: 973
- **함수**: _create_final_results()

## 🔍 원인 분석
### 직접 원인
'지불예상금액' 컬럼이 df_final_pivot에 존재하지 않음

### 근본 원인
'국세청공급가액'과 '국세청세액' 컬럼에 NaN 값이 많아 계산 결과도 NaN이 됨

### 재현 조건
1. 대사 실행
2. _create_final_results() 메서드 실행 시 오류

## 💡 해결 방안
### 즉각적인 수정
```python
# 수정 전 (line 849)
self.df_final_pivot["지불예상금액"] = self.df_final_pivot["국세청공급가액"] + self.df_final_pivot["국세청세액"]

# 수정 후
self.df_final_pivot["국세청공급가액"] = self.df_final_pivot["국세청공급가액"].fillna(0)
self.df_final_pivot["국세청세액"] = self.df_final_pivot["국세청세액"].fillna(0)
self.df_final_pivot["지불예상금액"] = self.df_final_pivot["국세청공급가액"] + self.df_final_pivot["국세청세액"]
```

## ✅ 파일 업로드 백그라운드 처리 확인
### main_window_v2.py
- **FileValidationThread** 클래스 추가 ✅
- **백그라운드 Excel 읽기** 구현 ✅
- **UI 블로킹 문제 해결** ✅

### 처리 흐름
1. 파일 선택 → UI 즉시 응답
2. '🔄 검증중...' 상태 표시
3. 백그라운드에서 Excel 파일 읽기
4. 완료 후 시그널로 UI 업데이트

## 📊 검증 방법
1. 프로그램 재시작
2. 5개 파일 모두 업로드
3. 대사 실행
4. 에러 없이 완료 확인

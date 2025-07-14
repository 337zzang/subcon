# 🎨 태스크 설계서

## 📋 기본 정보
- **프로젝트**: subcon
- **플랜**: 캐시 기능 및 날짜 처리 오류 수정
- **태스크 번호**: 02
- **태스크 ID**: b79483ad-3438-4ecc-8163-7951fff36fe0
- **태스크명**: 국세청작성일 날짜 처리 오류 분석 및 수정
- **작성일**: 2025-07-14
- **작성자**: AI Assistant
- **문서 경로**: C:\Users\Administrator\Desktop\subcon\docs\design\cache_and_date_fix_task02_date_processing_design_20250714.md

## 🎯 설계 목적
### 요구사항
노트북과 동일한 구조로 대사를 처리하고, 날짜 처리 부분도 노트북의 데이터프레임 조정 부분과 동일하게 구현해야 합니다.

### AI의 이해
현재 문제:
1. MultiIndex 컬럼 처리로 '국세청작성일'이 'nan_작성일'로 변환됨
2. 하드코딩된 컬럼 매핑으로 인한 KeyError
3. None 타입 날짜 처리 시 'total_seconds' 에러

### 해결하려는 문제
1. 매입세금계산서의 MultiIndex 컬럼 올바른 처리
2. 동적 컬럼 매핑으로 하드코딩 제거
3. None 타입 날짜에 대한 안전한 처리

## 🔍 현재 시스템 분석
### 문제가 되는 코드
```python
# 현재: 하드코딩된 매핑
column_mapping = {
    '국세청승인번호': '국세청승인번호',
    '업체사업자번호': '업체사업자번호',
    '국세청작성일': 'nan_작성일',  # 잘못된 매핑!
    '국세청발급일': 'nan_발급일'     # 잘못된 매핑!
}
```

### 노트북의 원래 방식
```python
# 노트북: MultiIndex 처리 후 동적 매핑
# 1. MultiIndex 평탄화
df.columns = [col if isinstance(col, str) else col[0] for col in df.columns]

# 2. 실제 컬럼명 확인
actual_columns = df.columns.tolist()

# 3. 패턴 매칭으로 컬럼 찾기
date_columns = [col for col in actual_columns if '작성일' in col]
```

## 💡 구현 방향
### 접근 방법
1. **MultiIndex 컬럼 처리 개선**
   ```python
   def flatten_multiindex_columns(df):
       '''MultiIndex 컬럼을 안전하게 평탄화'''
       if isinstance(df.columns, pd.MultiIndex):
           # 첫 번째 레벨만 사용 (노트북 방식)
           df.columns = [col[0] for col in df.columns.values]
       return df
   ```

2. **동적 컬럼 매핑**
   ```python
   def find_column_by_pattern(df, patterns):
       '''패턴으로 컬럼 찾기'''
       for pattern in patterns:
           matches = [col for col in df.columns if pattern in str(col)]
           if matches:
               return matches[0]
       return None

   # 사용 예
   작성일_컬럼 = find_column_by_pattern(df, ['국세청작성일', '작성일', '작성날짜'])
   발급일_컬럼 = find_column_by_pattern(df, ['국세청발급일', '발급일', '발급날짜'])
   ```

3. **안전한 날짜 처리**
   ```python
   def safe_date_conversion(series):
       '''None과 timezone을 안전하게 처리'''
       if series is None or series.isna().all():
           return None

       # datetime 변환
       converted = pd.to_datetime(series, errors='coerce')

       # timezone 제거 (있는 경우)
       if hasattr(converted, 'dt') and hasattr(converted.dt, 'tz'):
           converted = converted.dt.tz_localize(None)

       return converted
   ```

### 주요 변경사항
1. **reconciliation_service_v2.py - _process_tax_invoices() 수정**
   ```python
   # MultiIndex 처리 개선
   if isinstance(self.df_tax_hifi.columns, pd.MultiIndex):
       self.df_tax_hifi.columns = [col[0] for col in self.df_tax_hifi.columns.values]

   # 동적 컬럼 찾기
   작성일_컬럼 = find_column_by_pattern(self.df_tax_hifi, ['국세청작성일', '작성일'])
   발급일_컬럼 = find_column_by_pattern(self.df_tax_hifi, ['국세청발급일', '발급일'])

   # 안전한 매핑
   if 작성일_컬럼 and 발급일_컬럼:
       column_mapping = {
           '국세청승인번호': '국세청승인번호',
           '업체사업자번호': '업체사업자번호',
           '국세청작성일': 작성일_컬럼,
           '국세청발급일': 발급일_컬럼
       }
   ```

2. **날짜 처리 로직 개선**
   ```python
   # 작성년도, 작성월 추출
   if '국세청작성일' in self.df_tax_new.columns:
       date_col = safe_date_conversion(self.df_tax_new['국세청작성일'])
       if date_col is not None:
           self.df_tax_new['작성년도'] = date_col.dt.year
           self.df_tax_new['작성월'] = date_col.dt.month
       else:
           # 계산서작성일 사용 (폴백)
           self._use_fallback_date()
   ```

## ⚠️ 영향도 분석
### 직접 영향
- **변경 파일**: 
  - src/services/reconciliation_service_v2.py (_process_tax_invoices, _process_matching)
- **새 파일**: 없음
- **삭제 파일**: 없음

### 간접 영향
- **안정성**: 크게 향상 (동적 매핑으로 컬럼명 변경에 대응)
- **성능**: 변화 없음
- **정확도**: 향상 (날짜 처리 오류 해결)

### 하위 호환성
완전히 유지됨. 기존 데이터도 정상 처리됨.

## 🛡️ 리스크 관리
| 리스크 | 가능성 | 영향도 | 대응 방안 |
|--------|--------|--------|-----------|
| 컬럼명 패턴 불일치 | 낮음 | 높음 | 다양한 패턴 추가 |
| 날짜 형식 불일치 | 중간 | 중간 | pd.to_datetime의 format 옵션 활용 |
| None 타입 처리 | 낮음 | 낮음 | 모든 단계에서 None 체크 |

## 📊 예상 결과
### 성공 기준
- [x] MultiIndex 컬럼 정상 처리
- [x] 국세청작성일 정상 인식
- [x] 날짜 변환 에러 없음
- [x] 대사 처리 정상 작동

### 예상 소요 시간
- 구현: 30분
- 테스트: 20분
- 문서화: 10분

## ✅ 검증 계획
### 테스트 시나리오
1. MultiIndex 컬럼 파일 테스트
2. 다양한 날짜 형식 테스트
3. None 값 포함 데이터 테스트
4. 전체 대사 프로세스 테스트

### 디버그 로그 확인
```
✅ 세금계산서 처리 완료: 85건
⚠️ 날짜 변환 경고: [해결됨]
✅ 국세청작성일 정상 사용
```

## 📚 참고 자료
- pandas MultiIndex 문서
- pd.to_datetime 옵션
- 노트북의 원래 구조

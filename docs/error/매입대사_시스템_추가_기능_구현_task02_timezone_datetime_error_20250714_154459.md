# 🔴 에러 분석 보고서

## 🚨 에러 개요
- **발생 시간**: 2025-07-14 15:44:59
- **플랜**: 매입대사 시스템 추가 기능 구현
- **태스크 번호**: 02
- **태스크 ID**: 8b1c725c-6c70-4801-af84-eb9f741bba92
- **에러 타입**: timezone_datetime_error
- **심각도**: HIGH
- **영향 범위**: 세금계산서 처리 → 대사 처리 전체
- **문서 경로**: `docs/error/매입대사_시스템_추가_기능_구현_task02_timezone_datetime_error_20250714_154459.md`

## 📍 에러 상세
### 주요 에러 메시지
```
'NoneType' object has no attribute 'total_seconds'
```

### SettingWithCopyWarning
```
self.df_tax['협력사코드'] = self.df_tax['협력사코드'].astype(str)
```

### 스택 트레이스
```python
File "tzconversion.pyx", line 90, in pandas._libs.tslibs.tzconversion.Localizer.__cinit__
File "timezones.pyx", line 305, in pandas._libs.tslibs.timezones.get_dst_info
AttributeError: 'NoneType' object has no attribute 'total_seconds'
```

### 발생 위치
- **파일**: src/services/reconciliation_service_v2.py
- **라인**: 412-413 (df_tax_new['국세청작성일'].dt.year)
- **함수**: _process_matching()

## 🔍 원인 분석
### 직접 원인
1. **Timezone 처리 오류**: 
   - `pd.to_datetime()` 변환 후 timezone 정보가 None인 경우 발생
   - `국세청작성일` 컬럼의 datetime 객체가 불완전하게 생성됨

2. **DataFrame 뷰 수정**:
   - `self.df_tax = self.df_num[required_cols]`로 생성된 뷰를 직접 수정
   - pandas의 SettingWithCopyWarning 발생

### 근본 원인
1. **불안전한 datetime 변환**: 
   - timezone 정보 확인 없이 datetime 접근
   - None 값에 대한 예외 처리 부족

2. **DataFrame 복사본 미생성**:
   - 뷰 객체를 복사본으로 착각하여 직접 수정

## 💡 해결 방안
### 즉각적인 수정
```python
# 수정 전 (문제 코드)
self.df_tax = self.df_num[required_cols]
self.df_tax['협력사코드'] = self.df_tax['협력사코드'].astype(str)

# datetime 접근
self.df_tax_new['작성년도'] = self.df_tax_new['국세청작성일'].dt.year

# 수정 후 (해결 코드)
self.df_tax = self.df_num[required_cols].copy()  # 명시적 복사
self.df_tax['협력사코드'] = self.df_tax['협력사코드'].astype(str)

# 안전한 datetime 접근
if '국세청작성일' in self.df_tax_new.columns and not self.df_tax_new['국세청작성일'].isna().all():
    try:
        # timezone 정보 안전하게 제거
        if hasattr(self.df_tax_new['국세청작성일'].dtype, 'tz') and self.df_tax_new['국세청작성일'].dtype.tz is not None:
            self.df_tax_new['국세청작성일'] = self.df_tax_new['국세청작성일'].dt.tz_localize(None)
        self.df_tax_new['작성년도'] = self.df_tax_new['국세청작성일'].dt.year
        self.df_tax_new['작성월'] = self.df_tax_new['국세청작성일'].dt.month
    except Exception as e:
        # fallback to 계산서작성일
        print(f"⚠️ 국세청작성일 사용 불가, 계산서작성일 사용: {str(e)}")
        self.df_tax_new['계산서작성일'] = pd.to_datetime(self.df_tax_new['계산서작성일'], errors='coerce')
        self.df_tax_new['작성년도'] = self.df_tax_new['계산서작성일'].dt.year
        self.df_tax_new['작성월'] = self.df_tax_new['계산서작성일'].dt.month
else:
    # 국세청작성일이 없거나 모두 None인 경우
    print("⚠️ 국세청작성일 데이터 없음, 계산서작성일 사용")
    self.df_tax_new['계산서작성일'] = pd.to_datetime(self.df_tax_new['계산서작성일'], errors='coerce')
    self.df_tax_new['작성년도'] = self.df_tax_new['계산서작성일'].dt.year
    self.df_tax_new['작성월'] = self.df_tax_new['계산서작성일'].dt.month
```

### 수정 이유
1. **DataFrame 복사본 생성**: `.copy()` 메서드로 SettingWithCopyWarning 해결
2. **안전한 datetime 접근**: None 값 및 timezone 정보 확인 후 접근
3. **Fallback 로직 강화**: 국세청작성일 실패 시 계산서작성일로 안전하게 대체

## 🛡️ 예방 조치
### 코드 레벨
- DataFrame 조작 시 항상 `.copy()` 사용
- datetime 컬럼 접근 전 null 값 및 타입 확인
- timezone 정보 처리 로직 표준화

### 프로세스 레벨  
- 데이터 전처리 단계에서 datetime 형식 검증 강화
- 단위 테스트에 timezone 관련 케이스 추가

## ✅ 검증 방법
### 테스트 코드
```python
def test_datetime_processing():
    # timezone 있는 경우
    df_test = pd.DataFrame({
        '국세청작성일': pd.to_datetime(['2024-01-31'], utc=True)
    })
    # 에러가 발생하지 않아야 함
    result = safe_extract_year_month(df_test, '국세청작성일')
    assert result is not None

    # None 값인 경우  
    df_test2 = pd.DataFrame({
        '국세청작성일': [None, None]
    })
    # fallback이 작동해야 함
    result2 = safe_extract_year_month(df_test2, '국세청작성일', fallback='계산서작성일')
    assert result2 is not None
```

### 검증 체크리스트
- [ ] SettingWithCopyWarning 더 이상 발생하지 않음
- [ ] timezone 에러 해결됨  
- [ ] 관련 기능 정상 작동
- [ ] 성능 저하 없음
- [ ] 새로운 에러 미발생

## 📊 영향도 평가
- **수정 필요 파일**: src/services/reconciliation_service_v2.py
- **예상 작업 시간**: 30분
- **위험도**: LOW (안전한 수정)

## 📝 추가 개선 사항
1. **datetime 처리 유틸리티 함수 생성**
2. **데이터 검증 로직 강화** 
3. **로깅 개선** (어떤 날짜 컬럼을 사용했는지 명확히 기록)

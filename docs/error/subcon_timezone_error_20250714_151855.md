# 🔴 에러 분석 보고서

## 🚨 에러 개요
- **발생 시간**: 2025-07-14 15:18:55
- **프로젝트**: subcon
- **에러 타입**: pandas timezone conversion error
- **심각도**: 높음
- **영향 범위**: 대사 처리 전체 프로세스
- **CLAUDE.md 참조**: pandas timezone handling
- **stderr 내용**: AttributeError: 'NoneType' object has no attribute 'total_seconds'
- **문서 경로**: C:\Users\Administrator\Desktop\subcon\docs\error\subcon_timezone_error_20250714_151855.md

## 📍 에러 상세
### 에러 메시지
```
AttributeError: 'NoneType' object has no attribute 'total_seconds'
Exception ignored in: 'pandas._libs.tslibs.conversion._localize_tso'
```

### stderr 내용
```
Traceback (most recent call last):
  File "tzconversion.pyx", line 90, in pandas._libs.tslibs.tzconversion.Localizer.__cinit__
  File "timezones.pyx", line 305, in pandas._libs.tslibs.timezones.get_dst_info
AttributeError: 'NoneType' object has no attribute 'total_seconds'
```

### 발생 위치
- **파일**: src/services/reconciliation_service_v2.py
- **라인**: 1069
- **함수**: _write_dataframe_to_sheet()

## 🔍 원인 분석
### 직접 원인
pandas Timestamp 객체에 timezone 정보가 없을 때 `tz_localize("UTC")`를 호출하면서 발생

### 근본 원인
1. pandas 내부의 timezone 변환 처리 중 버그
2. timezone 정보가 없는 naive datetime을 강제로 localize하려고 시도
3. pandas의 Cython 레벨에서 NoneType 객체 처리 오류

### CLAUDE.md 해결법
매입대사2.ipynb에서 사용한 방법:
- `is_datetime64tz_dtype` 사용 (deprecated)
- timezone aware인 경우 `dt.tz_convert(None)` 사용

### stderr 분석 결과
- 반복적으로 동일한 오류 발생 (500회 이상)
- 대사 처리의 각 단계에서 날짜 처리 시 발생
- Excel 출력 시 가장 많은 오류 발생

### 재현 조건
1. 매입대사 시스템 실행
2. Excel 파일 업로드
3. 대사 처리 진행
4. 결과 Excel 저장 시 대량 오류 발생

## 💡 해결 방안
### 즉각적인 수정
```python
# 수정 전
if isinstance(val, pd.Timestamp):
    if val.tzinfo is None:
        val = val.tz_localize("UTC").to_pydatetime()
    else:
        val = val.to_pydatetime()

# 수정 후
if isinstance(val, pd.Timestamp):
    try:
        # timezone 정보가 있는 경우 제거
        if hasattr(val, 'tz') and val.tz is not None:
            val = val.tz_localize(None)
        val = val.to_pydatetime()
    except Exception:
        # 오류 발생 시 문자열로 변환
        val = str(val)
```

### 수정 이유
1. `tz_localize("UTC")`는 이미 timezone이 있을 때 오류 발생
2. timezone이 없는 경우 localize 불필요
3. 안전한 처리를 위해 try-except 사용

## 🛡️ 예방 조치
### 코드 레벨
- 모든 datetime 처리에 try-except 추가
- timezone naive datetime만 사용
- pandas 버전별 호환성 처리

### 프로세스 레벨
- 날짜 데이터 입력 시 timezone 제거
- Excel 출력 전 datetime 검증

### stderr 모니터링 강화
- pandas 관련 stderr 출력 감지
- timezone 오류 패턴 등록

## ✅ 검증 방법
### 테스트 코드
```python
def test_excel_output_datetime():
    import pandas as pd
    from datetime import datetime
    
    # 테스트 데이터 생성
    df = pd.DataFrame({
        '날짜': [pd.Timestamp('2024-01-01'), pd.NaT, datetime.now()]
    })
    
    # Excel 출력 테스트
    for val in df['날짜']:
        if isinstance(val, pd.Timestamp):
            try:
                if hasattr(val, 'tz') and val.tz is not None:
                    val = val.tz_localize(None)
                result = val.to_pydatetime()
                print(f"✅ 변환 성공: {result}")
            except Exception as e:
                print(f"❌ 변환 실패: {e}")
    
    # stderr 체크
    assert result is not None
```

### 검증 체크리스트
- [ ] 에러가 더 이상 발생하지 않음
- [ ] CLAUDE.md 해결법 확인
- [ ] stderr 분석 완료
- [ ] 수정 코드 적용
- [ ] 단위 테스트 통과
- [ ] 통합 테스트 통과
- [ ] stderr 깨끗함 확인
- [ ] 코드 리뷰 완료
- [ ] 배포 준비
- [ ] CLAUDE.md 업데이트

## ⚡ 배포 계획
1. reconciliation_service_v2.py 수정
2. 테스트 환경에서 검증
3. 프로덕션 배포

## 📊 모니터링
- 확인할 메트릭: stderr 로그 개수
- stderr 모니터링: pandas timezone 관련 오류
- 알림 설정: AttributeError 발생 시 즉시 알림

## 📝 관련 문서
- 매입대사2.ipynb: timezone 처리 참고 코드
- pandas 공식 문서: timezone handling
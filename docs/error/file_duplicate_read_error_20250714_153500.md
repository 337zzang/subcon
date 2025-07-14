# 🔴 에러 분석 보고서

## 🚨 에러 개요
- **발생 시간**: 2025-07-14 15:35:08
- **플랜**: 매입대사 시스템 추가 기능 구현
- **태스크 번호**: N/A (버그 수정)
- **태스크 ID**: N/A
- **에러 타입**: file_duplicate_read_error
- **심각도**: 중간
- **영향 범위**: 파일 업로드 성능 및 메모리 사용량
- **CLAUDE.md 참조**: 파일 캐싱 및 중복 읽기 방지
- **stderr 출력**: 없음
- **문서 경로**: C:\Users\Administrator\Desktop\subcon\docs\error\file_duplicate_read_error_20250714_153500.md

## 📍 에러 상세
### 에러 메시지
```
[INFO] 'C:/Users/Administrator/Desktop/subcontract/data/협력사단품별매입(최종작업용).xlsx' 읽는 중…
[INFO] 'data\기준(최종작업용).xlsx' 읽는 중…
```

### stderr 내용
없음

### 발생 위치
- **파일**: src/ui/upload_main_window.py
- **라인**: FileUploadThread.validate_file() 및 DataLoadThread.run()
- **함수**: 파일 검증 및 데이터 로드

## 🔍 원인 분석
### 직접 원인
1. FileUploadThread에서 파일 검증을 위해 read_excel_data 호출
2. DataLoadThread에서 실제 데이터 로드를 위해 다시 읽기
3. 경로 처리 차이로 인한 중복 (절대경로 vs 상대경로)

### 근본 원인
- 파일 검증과 데이터 로드가 분리되어 있음
- 읽은 데이터를 캐싱하지 않고 버림
- 파일 경로 정규화 부재

### CLAUDE.md 해결법
파일 캐싱 메커니즘 구현으로 중복 읽기 방지

### 재현 조건
1. 매입대사 시스템 실행
2. Excel 파일 업로드
3. 동일 파일이 2번 읽히는 것 확인

## 💡 해결 방안
### 즉각적인 수정
```python
# DataManager에 파일 캐시 추가
class DataManager:
    def __init__(self):
        # 기존 코드...
        self._file_cache = {}  # 파일 캐시 추가

    def cache_file_data(self, file_path: str, data: pd.DataFrame):
        '''파일 데이터 캐싱'''
        normalized_path = os.path.normpath(file_path)
        self._file_cache[normalized_path] = data

    def get_cached_data(self, file_path: str) -> Optional[pd.DataFrame]:
        '''캐싱된 데이터 반환'''
        normalized_path = os.path.normpath(file_path)
        return self._file_cache.get(normalized_path)
```

### 수정 이유
- 한 번 읽은 파일은 메모리에 캐싱
- 재사용 시 파일 I/O 없이 메모리에서 직접 사용
- 경로 정규화로 중복 방지

## 🛡️ 예방 조치
### 코드 레벨
- 파일 읽기 전 캐시 확인 로직 추가
- 경로 정규화 함수 사용
- 메모리 사용량 모니터링

### 프로세스 레벨
- 대용량 파일 처리 시 캐시 관리 정책
- 메모리 부족 시 캐시 비우기

### stderr 모니터링 강화
- 파일 읽기 시작/종료 로그 추가
- 중복 읽기 감지 로직

## ✅ 검증 방법
### 테스트 코드
```python
def test_file_caching():
    data_manager = DataManager()

    # 첫 번째 읽기
    df1 = read_excel_data("test.xlsx")
    data_manager.cache_file_data("test.xlsx", df1)

    # 캐시에서 가져오기
    df2 = data_manager.get_cached_data("test.xlsx")
    assert df2 is df1  # 동일한 객체 확인
```

### 검증 체크리스트
- [ ] 파일이 한 번만 읽힘
- [ ] 캐싱된 데이터 정상 사용
- [ ] 메모리 사용량 적정
- [ ] 성능 개선 확인

## 📊 영향도 평가
- **수정 필요 파일**: 3개 (data_manager.py, upload_main_window.py, excel_service.py)
- **예상 작업 시간**: 30분
- **위험도**: 낮음

## 📝 CLAUDE.md 업데이트
```markdown
# 파일 중복 읽기 방지
오류: 동일 파일을 여러 번 읽어 성능 저하
해결: DataManager에 파일 캐싱 메커니즘 구현
- cache_file_data(): 읽은 데이터 캐싱
- get_cached_data(): 캐시된 데이터 반환
- 경로 정규화로 중복 방지
```

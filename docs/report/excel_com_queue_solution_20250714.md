# 🔧 Excel COM 오류 해결: 큐 기반 메인 스레드 처리

## 📋 요약
- **문제**: 백그라운드 스레드에서 pywin32 Excel COM 객체 사용 시 오류
- **원인**: COM 객체는 메인 스레드에서만 안전하게 작동
- **해결**: 큐(Queue)를 사용해 메인 스레드에서만 Excel 읽기
- **작성일**: 2025-07-14 14:49
- **문서 경로**: docs/report/excel_com_queue_solution_20250714.md

## 🚨 문제 상황
```
(-2147417848, '호출된 개체가 해당 클라이언트로부터 연결이 끊겼습니다.', None, None)
```
- 백그라운드 스레드에서 pywin32로 Excel 파일을 읽을 때 발생
- 여러 스레드가 동시에 COM 객체 접근 시 충돌

## ✅ 해결 방법: 큐 기반 아키텍처

### 1. 전역 큐와 결과 저장소
```python
# 전역 큐와 결과 딕셔너리
excel_read_queue = queue.Queue()
excel_read_results = {}
```

### 2. FileValidationThread (백그라운드)
```python
def run(self):
    # 큐에 읽기 요청 추가
    excel_read_queue.put({
        'id': self.request_id,
        'file_path': self.file_path,
        'file_type': self.file_type
    })

    # 결과를 기다림
    while elapsed < timeout:
        if self.request_id in excel_read_results:
            result = excel_read_results.pop(self.request_id)
            # 결과 처리...
```

### 3. ImprovedMainWindow (메인 스레드)
```python
def __init__(self):
    # Excel 읽기 큐 처리를 위한 타이머
    self.excel_queue_timer = QTimer()
    self.excel_queue_timer.timeout.connect(self.process_excel_queue)
    self.excel_queue_timer.start(100)  # 100ms마다 큐 체크

def process_excel_queue(self):
    '''Excel 읽기 큐 처리 (메인 스레드에서 실행)'''
    request = excel_read_queue.get_nowait()

    # 메인 스레드에서 Excel 파일 읽기
    df = read_excel_data(file_path)  # COM 객체 안전!

    # 결과 저장
    excel_read_results[request_id] = {
        'success': True,
        'data': df
    }
```

## 📊 처리 흐름

1. **파일 선택** (UI)
2. **FileValidationThread 시작** (백그라운드)
3. **큐에 요청 추가** (백그라운드 → 큐)
4. **메인 스레드가 큐 처리** (QTimer)
5. **Excel 파일 읽기** (메인 스레드, COM 안전)
6. **결과 저장** (excel_read_results)
7. **백그라운드가 결과 수신** (폴링)
8. **UI 업데이트** (시그널)

## 🎯 장점

1. **COM 안전성**: Excel COM 객체가 항상 메인 스레드에서만 실행
2. **UI 응답성**: 백그라운드 처리로 UI 블로킹 없음
3. **동시성 처리**: 여러 파일을 순차적으로 안전하게 처리
4. **타임아웃 지원**: 30초 타임아웃으로 무한 대기 방지

## 📈 성능 영향

- **처리 지연**: 최대 100ms (타이머 주기)
- **메모리 사용**: 최소 (큐와 결과 딕셔너리만 사용)
- **CPU 사용**: 낮음 (100ms 주기 폴링)

## ⚠️ 주의사항

1. 프로그램 종료 시 타이머 정리 필수
2. 큐가 가득 차지 않도록 주의
3. 결과 딕셔너리 메모리 관리 필요

## 🔍 디버깅 팁

```python
# 큐 상태 확인
print(f"큐 크기: {excel_read_queue.qsize()}")
print(f"대기 중인 결과: {len(excel_read_results)}")
```

## ✅ 결론

큐 기반 아키텍처로 COM 객체 충돌 문제를 완전히 해결했습니다. 
이제 백그라운드에서도 안전하게 Excel 파일을 읽을 수 있으며, 
UI 응답성도 유지됩니다.

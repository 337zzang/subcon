# 📊 매입대사2.ipynb 분석 및 오류 정리

## 🎯 노트북과 현재 구현의 주요 차이점

### 1. 데이터 파일 구조
| 항목 | 노트북 | 현재 구현 | 차이점 |
|------|--------|----------|---------|
| 파일 수 | 6개 | 5개 | 임가공비 파일 미사용 |
| 파일 읽기 | 각 파일별 1회 | 2회 (업로드+대사) | 중복 읽기 |
| Grand Total | 첫 행 제거 | 처리 없음 | 데이터 오류 가능 |

### 2. 날짜 처리 오류 분석

#### 2.1 MultiIndex 컬럼 문제
```python
# 노트북의 올바른 처리
df_tax_hifi.columns = [col[0] if pd.isna(col[1]) else f"{col[0]}_{col[1]}" for col in df_tax_hifi.columns]

# 현재 문제: 하드코딩된 매핑
column_mapping = {
    '국세청작성일': 'nan_작성일',  # ❌ 잘못된 매핑
    '국세청발급일': 'nan_발급일'   # ❌ 잘못된 매핑
}
```

#### 2.2 날짜 변환 오류
```
⚠️ 날짜 변환 경고: 'NoneType' object has no attribute 'total_seconds'
```
- 원인: None 값에 대한 처리 누락
- 해결: pd.to_datetime의 errors='coerce' 사용 + None 체크

#### 2.3 Timezone 처리
```python
# 노트북: 개별 timezone 제거
if pd.api.types.is_datetime64tz_dtype(df['날짜']):
    df['날짜'] = df['날짜'].dt.tz_convert(None)
```

### 3. 대사 처리 로직 차이

#### 3.1 데이터 전처리
```python
# 노트북 방식
1. 협력사단품별매입 그룹화 → 피벗
2. 기준 데이터와 Inner Join
3. 협력사별 재그룹화 → 최종 피벗
4. 0원 제외

# 현재: 직접 처리 (중간 과정 누락 가능)
```

#### 3.2 대사 순서
1. **금액대사**: 1:1 정확한 매칭
2. **금액대사(수기확인)**: 면과세 조건 제외
3. **순차대사**: 1:N FIFO 방식
4. **부분대사**: 금액이 더 큰 경우
5. **수기확인**: 복수 합산

### 4. 주요 오류 패턴

#### 4.1 데이터 타입 오류
```python
# 협력사코드/단품코드 타입 통일 필요
df['협력사코드'] = df['협력사코드'].astype(int).astype(str)
```

#### 4.2 컬럼 존재 여부 체크 누락
```python
# 안전한 처리
if '국세청작성일' in df.columns and not df['국세청작성일'].isna().all():
    # 처리
else:
    # 폴백: 계산서작성일 사용
```

#### 4.3 날짜 처리 폴백 로직
```python
try:
    # 국세청작성일 사용
    df['작성년도'] = df['국세청작성일'].dt.year
except:
    # 계산서작성일 사용
    df['작성년도'] = df['계산서작성일'].dt.year
```

### 5. 해결 방안

#### 5.1 파일 읽기 최적화
```python
# DataManager에 DataFrame 저장
class DataManager:
    def __init__(self):
        self.dataframes = {}  # 파일별 DataFrame 저장

    def set_dataframe(self, file_type, df):
        # Grand Total 행 제거
        if file_type == 'purchase_detail' and len(df) > 0:
            df = df.drop(0).reset_index(drop=True)
        self.dataframes[file_type] = df
```

#### 5.2 MultiIndex 컬럼 동적 처리
```python
def process_multiindex_columns(df):
    '''MultiIndex 컬럼을 안전하게 평탄화'''
    if isinstance(df.columns, pd.MultiIndex):
        # 노트북 방식 적용
        df.columns = [col[0] if pd.isna(col[1]) else f"{col[0]}_{col[1]}" 
                     for col in df.columns]
    return df

def find_date_columns(df):
    '''날짜 관련 컬럼 동적 탐색'''
    date_patterns = {
        '작성일': ['국세청작성일', '작성일', 'nan_작성일'],
        '발급일': ['국세청발급일', '발급일', 'nan_발급일']
    }

    found_columns = {}
    for key, patterns in date_patterns.items():
        for pattern in patterns:
            matching_cols = [col for col in df.columns if pattern in str(col)]
            if matching_cols:
                found_columns[key] = matching_cols[0]
                break

    return found_columns
```

#### 5.3 안전한 날짜 처리
```python
def safe_date_processing(df_tax_new):
    '''안전한 날짜 처리 with 폴백'''
    # 1차: 국세청작성일 시도
    if '국세청작성일' in df_tax_new.columns:
        df_tax_new['국세청작성일'] = pd.to_datetime(
            df_tax_new['국세청작성일'], errors='coerce'
        )

        # timezone 제거
        if hasattr(df_tax_new['국세청작성일'], 'dt'):
            if hasattr(df_tax_new['국세청작성일'].dt, 'tz'):
                df_tax_new['국세청작성일'] = df_tax_new['국세청작성일'].dt.tz_localize(None)

        # 유효성 체크
        if not df_tax_new['국세청작성일'].isna().all():
            df_tax_new['작성년도'] = df_tax_new['국세청작성일'].dt.year
            df_tax_new['작성월'] = df_tax_new['국세청작성일'].dt.month
            return True

    # 2차: 계산서작성일 폴백
    print("⚠️ 국세청작성일 사용 불가, 계산서작성일 사용")
    df_tax_new['계산서작성일'] = pd.to_datetime(
        df_tax_new['계산서작성일'], errors='coerce'
    )

    if not df_tax_new['계산서작성일'].isna().all():
        df_tax_new['작성년도'] = df_tax_new['계산서작성일'].dt.year
        df_tax_new['작성월'] = df_tax_new['계산서작성일'].dt.month
        return True

    # 3차: 현재 날짜 사용
    print("⚠️ 모든 날짜 사용 불가, 현재 년월 사용")
    now = datetime.now()
    df_tax_new['작성년도'] = now.year
    df_tax_new['작성월'] = now.month
    return False
```

### 6. 구현 체크리스트

- [ ] DataFrame 재사용으로 중복 읽기 제거
- [ ] Grand Total 행 제거 로직 추가
- [ ] MultiIndex 컬럼 동적 처리
- [ ] 날짜 컬럼 동적 탐색
- [ ] 안전한 날짜 변환 with 폴백
- [ ] Timezone 제거 로직
- [ ] 타입 변환 안전 처리
- [ ] 6개 파일 구조 지원 (임가공비 옵션)

### 7. 예상 효과

1. **성능 개선**: 파일 읽기 50% 감소
2. **안정성 향상**: 날짜 처리 오류 해결
3. **정확도 향상**: 노트북과 동일한 결과
4. **유지보수성**: 동적 처리로 컬럼명 변경 대응

---
*매입대사2.ipynb 분석 완료 - 2025-07-14*

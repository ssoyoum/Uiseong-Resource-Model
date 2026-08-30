# VWorld 공모전 데이터 확보 TODO

최종 확인일: 2026-08-30

## 자료 출처 우선순위

본 분석은 아래 순서로 자료를 채운다.

1. **VWorld 원자료**: 도로·생활SOC·공공·문화·관광시설의 1순위
2. **공공데이터 공식 원자료**: 인구·행정경계·시설 보완 자료의 2순위
3. **수동 다운로드 자료**: VWorld 로그인이나 대용량 파일 문제로 자동 확보가 안 될 때 공식 링크에서 직접 확보
4. **OSM·WorldPop**: 참고·교차검증·분포 시각화용. VWorld 또는 국내 공식 공공데이터를 확보한 것으로 간주하지 않음

현재 상태: 행정안전부 인구는 공공데이터 원자료 확보·처리 완료. VWorld UQ164·UO601 시설 원자료는 의성군 68개를 처리했고, UQ151 도로 공간파일은 아직 미확보 상태다.

## 현재 확보·처리 완료

- [x] 행정안전부 주민등록 연령별 인구 CSV 2024년 12월 확보
- [x] 행정안전부 주민등록 연령별 인구 CSV 2025년 12월 확보
- [x] 의성군 코드 `4773` 기준 읍·면 18개 추출
- [x] 청년 기준 확정: 만 19~39세
- [x] 고령 기준 확정: 만 65세 이상
- [x] 2024→2025 인구증감 산출
- [x] `data/processed/population/uiseong_population.csv` 생성
- [x] 인구 지도·요약 JSON 파이프라인 연결

재다운로드가 필요하면 다음 명령을 실행한다.

```bash
python analysis/acquire_population.py
python analysis/run_competition_pipeline.py
```

인구 출처: [행정안전부 지역별 연령별 주민등록 인구현황](https://www.data.go.kr/data/3033304/fileData.do?recommendDataYn=Y), [주민등록 인구통계 연령별 인구현황](https://jumin.mois.go.kr/ageStatMonth.do). 메타데이터는 `data/manifests/population_sources.csv`에 기록했다.

## 참고용 자료 확보 완료

- [x] WorldPop Global2 한국 100m 인구 raster 2020 constrained 확보
- [x] 원자료 보관: `data/raw/population/worldpop/kor_pop_2020_CN_100m_R2025A_v1.tif`
- [x] 다운로드 재현 스크립트: `python analysis/acquire_worldpop.py`
- [x] 출처·접근일·SHA-256·라이선스 링크를 `data/manifests/worldpop_sources.csv`에 기록

비고: WorldPop은 약 100m(3 arc-second) 격자별 추정 인구수다. 국내 주민등록 인구와 산출모형·기준시점이 다르므로 공모전의 공식 인구값을 대체하지 않고, 인구분포 비교·Buffer 참고·시각화용으로만 사용한다. 원자료 라이선스는 [WorldPop licence](https://www.worldpop.org/data/licence.txt)를 확인한다.

## 직접 확보해야 하는 자료

### 1. VWorld 도로 데이터 — 최우선

- [ ] VWorld 계정으로 로그인 후 도로 SHP 다운로드
- [ ] 공식 데이터 페이지: [국토교통부\_도로(현황)](https://www.vworld.kr/dtmk/dtmk_ntads_s002.do?dsId=30074)
- [ ] 파일명: `C_UQ151.zip` 또는 다운로드 시점의 동일 도로 현황 파일
- [ ] 다운로드 파일을 기존 `vworld/`에 보관
- [ ] 압축 해제 후 SHP·SHX·DBF·PRJ가 모두 있는지 확인
- [ ] 원본 좌표계가 EPSG:5174인지 확인
- [ ] VWorld 레이어명, 다운로드일, 제공기관, 이용조건을 `data/manifests/vworld_sources.csv`에 입력
- [ ] 전국 원본이면 의성군 경계로 Clip하여 `data/processed/roads/uiseong_roads.gpkg` 생성
- [ ] 도로 데이터 확보 후 `python analysis/run_competition_pipeline.py`를 실행하여 427개 최근접거리 계산

참고: 공공데이터포털 설명상 이 데이터는 무료 SHP이며 VWorld 다운로드 페이지로 연결되지만, 현재 확인 시 로그인 후 다운로드가 필요하다. 이용허락은 출처표시·상업적 이용금지·변경금지 조건을 확인해야 한다.

### 2. VWorld 생활·공공·문화·관광시설 — 우선순위 2

- [x] VWorld `LSMD_CONT_UQ164_5174_경북.zip` 선택 — 공공·교육·문화·안전시설 Polygon
- [x] VWorld `LSMD_CONT_UO601_5174_경북.zip` 선택 — 관광지·관광특구 Polygon
- [x] 의성군 코드 `47730` 선별 및 EPSG:5174 변환
- [x] 의성군 경계 Clip 결과를 `data/processed/facilities/uiseong_facilities.gpkg`로 저장
- [x] `facility_count_500m`, `facility_count_1000m` 계산
- [x] 전체 파일 분류·제외사유를 `data/analysis/vworld_layer_inventory.json`에 기록

현재 처리 결과: VWorld 시설 68개(UQ164 67개 + UO601 1개). `facility_category`는 관광·문화·교육·보건·공공안전·체육·기타 공공시설로 구분했다.

비고: 건축물·하천·토지 자료는 시설 Point나 도로 중심선의 대체재로 사용하지 않았다. 현재 시설자료는 저장소의 `vworld/`에 있는 UQ164·UO601 원자료를 기준으로 처리했다.

### 3. 인구 격자 데이터 — Buffer 인구 산출용

- [ ] 읍·면 총계가 아닌 실제 격자 단위 인구자료 확보 여부 확인
- [x] WorldPop 한국 100m 격자 참고자료 확보 (`data/raw/population/worldpop/`)
- [ ] 국내 공식 인구 격자자료 확보 및 WorldPop과 별도 기준으로 관리
- [ ] 가능하면 100m 또는 500m 격자, 기준연도, 인구·청년·고령 필드가 있는 자료 사용
- [ ] 격자 데이터가 없으면 현재처럼 Buffer 안의 인구를 임의 배분하지 않음
- [ ] 확보 시 `data/raw/population/`에 보관하고 `pond_context_analysis.py`에 격자 Intersection 추가

비고: WorldPop 100m는 다운로드만 완료한 참고 raster다. 국내 공식 주민등록 격자와 기준·모형이 다르므로 현재 공식 Buffer 인구값은 계속 `DATA_NOT_AVAILABLE`로 둔다. WorldPop을 분석에 연결할 경우에도 `worldpop_population_500m`, `worldpop_population_1km`처럼 별도 필드명으로 구분한다.

### 4. 현장조사·관리상태 데이터 — 분류 고도화용

- [ ] 427개 시설 ID와 연결되는 관리상태, 보존가치, 현장사진/조사일 필드 정리
- [ ] 개인정보·연락처·개인 식별정보는 제외
- [ ] 시설 ID 매칭표를 만들고 `management`, `survey_status`, `heritage_note` 필드를 명시
- [ ] 출처와 조사 기준일을 README 또는 별도 manifest에 기록

## 아이디어 — 추가 검토 후 적용

### A. 생활SOC 2020 자료를 수요·입지 보조지표로 사용

대상 파일: `vworld/gb_r032.zip`, `vworld/gb_r033.zip`

- [ ] `gb_r032`의 `FAC_TYP`, `FAC_NM`, `GRADE_TYP`, `GRADE`, `GRID_ID` 의미와 등급 방향 확인
- [ ] `gb_r033`의 시·군·구별 `GRADE`가 어떤 입지분석 결과인지 정의서로 재확인
- [ ] 의성군을 포함하는 동일 자료의 최신/전국판 또는 의성군 Clip 자료 확보
- [ ] EPSG:4326을 EPSG:5174로 변환한 뒤 500m·1km Buffer와 Intersection
- [ ] `socs_grade_mean_500m`, `socs_high_grade_grid_count_1km`, `socs_context_status` 같은 별도 필드로 저장
- [ ] 시설 개수(`facility_count`)나 공공시설 원자료로 오인하지 않고, 생활SOC 수요·유인력·입지등급 보조변수로만 사용

현재 판단: **조건부 가능**. 정의서상 생활SOC 생활문화센터군의 유인력·수요도/입지분석 격자·Polygon 자료이지만, 현재 파일의 공간범위는 의성군을 포함하지 않아 그대로 사용할 수 없다. 의성군 범위 자료를 추가로 확보할 때만 적용한다.

### B. 교통문화지수를 의성군 전체 배경지표로 사용

대상 파일: `vworld/T_W_BASE_ART_CULT_IDX.zip`, `vworld/T_W_BASE_TRF_CULT_IDX.zip`

- [x] TXT를 UTF-8-SIG, `|` 구분자로 읽고 정의서의 컬럼명을 적용
- [x] `JIJACE_CD = 47730`(경북 의성군) 레코드만 추출
- [x] `T_W_BASE_ART_CULT_IDX`: 2014~2024 연도별 운전행태 관련 지표와 기타 문화지수 항목 확인
- [x] `T_W_BASE_TRF_CULT_IDX`: 2017~2024 연도별 운전행태·교통안전·보행·교통약자·문화 점수 및 순위 확인
- [x] 최근 연도 값과 기준연도를 `data/analysis/traffic_culture_context.json`에 저장
- [x] 공모전 `competition_metrics.json`에 군 단위 배경지표 상태 기록
- [x] 시설별 500m·1km 접근성이나 도로거리로 복제하지 않고 `uiseong_county_context`로 명확히 표시
- [x] 출처·작성기관·연도·컬럼정의를 별도 manifest에 기록

현재 판단: **적용 가능**. 의성군 코드 `47730` 레코드가 존재하며, 2024년 값까지 확인된다. 다만 공간해상도가 시·군·구 단위라서 개별 못의 접근성 우열이나 생활시설 개수를 설명하는 직접 변수로 사용하지 않고, 의성군 전체 교통·문화 환경의 참고지표로만 사용한다.

### C. 두 자료를 활용유형 분류에 넣는 방법

- [ ] 생활SOC 의성군 자료 확보 시 `B_ECO_EDUCATION`·`C_COMMUNITY` 분류의 보조 근거로 검토
- [ ] 교통문화지수는 `classification_reason`에 직접 점수판정으로 넣기보다 “의성군 단위 배경지표”로 별도 표시
- [ ] 임의 가중치를 새로 만들지 않고 변수분포·결측·연도 차이를 먼저 확인
- [ ] 2020 생활SOC와 2024 교통문화지수를 결합할 경우 기준연도 차이를 결과 설명에 명시
- [ ] 원자료 라이선스와 공모전 제출물 포함 가능 여부 확인

## 확보 후 반드시 할 일

- [x] 실제 VWorld 자료의 레이어·파일·의성군 범위 확인
- [x] VWorld 시설 CRS, geometry valid, 의성군 경계 밖 데이터 검증
- [ ] VWorld 원자료의 최종 라이선스·재배포 조건 확인
- [ ] 도로 거리 단위가 meter인지 확인
- [x] 500m·1km 면적 단위가 m²/ha인지 확인
- [ ] 인구 기준연도와 시설·도로 데이터 기준시점을 README에 함께 표시
- [ ] 도로·생활시설 원자료를 GitHub에 올릴 수 있는지 이용조건 확인
- [x] `data/analysis/validation_report.json`이 PASS인지 확인
- [ ] 분류 결과가 실제 근거를 갖는지 `classification_reason` 표본 검토
- [ ] `D_PRESERVATION` fallback 비율이 높으면 원자료 결측 원인과 개선방안 기록

## 현재 판단

- 인구 자료: 확보 완료, 분석 연결 완료
- 인구 원자료 보관: `data/raw/population/`(대용량 원본은 Git 추적 제외)
- 기존 농업지역: 기존 프로젝트 자료로 계산 가능하지만 VWorld 출처는 미확인
- VWorld 도로: 계정 로그인 및 대용량 SHP 다운로드 필요
- VWorld 생활시설: UQ164·UO601 확보·Clip·시설 Buffer 계산 완료
- 인구 Buffer: 국내 공식 격자자료 분석 연결 전이므로 공식 인구값은 `DATA_NOT_AVAILABLE`; WorldPop은 참고용 확보 완료
- 생활SOC 2020: 의성군 범위 자료 확보 전까지 아이디어로 보류
- 교통문화지수: 의성군 시군구 배경지표 추출·결과파일 연결 완료
- React/API/DB: 이번 데이터 확보 단계에서는 미적용

# 데이터 품질 관리

## 문서 요약

- Last updated: 2026-08-31 22:55:05 KST
- 주요 데이터셋 또는 snapshot: 의성군 못 427개, VWorld UQ164·UO601·UQ151, 행정안전부 주민등록 연령별 인구 2024-12·2025-12, SGIS 생활권역 주행인구 2024
- Analysis scope: 의성군 못의 생활시설·관광시설·도로 접근성·읍면 인구 맥락·SGIS 5/10분 생활권 인구·활용유형 분류
- Current validation status: 전체 파이프라인 PASS. `validation_report.json` PASS(좌표 중복 WARN 1건), 제출근거 검증 17 PASS / 0 WARN / 0 FAIL
- Open data-quality issues count: 5

이 문서는 코드 버그나 성능 병목이 아니라, 원자료의 구조·정의·범위·기준시점·공간 품질이 분석 해석에 미치는 영향을 관리한다. 날짜별 작업 내역은 루트 [`WORKLOG.md`](../WORKLOG.md)에 간단히 기록한다.

## 상태 기준

- Status: `Open`, `Investigating`, `Resolved`, `Accepted limitation`
- Impact: `Critical`, `High`, `Medium`, `Low`
- `DATA_NOT_AVAILABLE`은 값이 0이라는 뜻이 아니며, 원자료 미제공·위치 인식 실패·비밀보호 응답을 임의값으로 대체하지 않는다.

## 이슈 요약

| ID | Status | Impact | 핵심 이슈 | 다음 확인 시점 |
|---|---|---|---|---|
| DQ-001 | Open | High | 시설 좌표 품질·중복 좌표·대표점 | 좌표 보정 자료 확보 또는 원자료 갱신 시 |
| DQ-002 | Open | High | SGIS 경로망 위치 인식 실패 384건 | 좌표 보정 후 SGIS 재수집 시 |
| DQ-003 | Open | Medium | SGIS 생활권역은 생성됐으나 인구값이 없는 15건 | SGIS 재요청 또는 기준연도 갱신 시 |
| DQ-004 | Open | Medium | 공식 인구격자 원자료 부재 | 공식 격자 확보 시 |
| DQ-005 | Open | Medium | VWorld·기존 경계/농업자료 snapshot·라이선스 메타데이터 미완결 | 새 원자료·snapshot 반입 시 |
| DQ-006 | Resolved | Low | CP949 원자료와 UTF-8 파생자료의 인코딩 차이 | 새 CSV 추가 시 회귀 확인 |
| DQ-007 | Resolved | Medium | 분석 CRS·웹 CRS·SGIS 응답 CRS 및 geometry 처리 | 새 공간자료 추가 시 회귀 확인 |
| DQ-008 | Accepted limitation | Medium | 행정안전부·SGIS·VWorld 기준시점 차이 | 기준연도 변경 시 재검토 |
| DQ-009 | Accepted limitation | Medium | 행정 읍면 총계·SGIS 주행생활권·격자 Buffer의 정의 차이 | 제출문서 수치 대조 시 |
| DQ-010 | Resolved | Low | 시설 ID·필수 필드·출력 스키마 검증 | 새 시설 snapshot 반입 시 |

## 상세 이슈

### DQ-001 — 시설 좌표 품질·중복 좌표

- Status: `Open`
- Impact: `High`
- 발견일: 2026-08-31
- 대상 데이터셋: `data/processed/ponds.csv`, `data/analysis/coordinate_quality_audit.csv`, SGIS 생활권역 입력 좌표
- 증상: 427개 시설 중 정좌표 382개, 인근좌표 4개, 시군구 대표좌표 41개다. 고유 좌표는 386개이고, 중복 좌표 그룹 2개에 43개 시설이 포함된다. 실제 보정 완료 시설은 0개이며, 검증 좌표 기준 신뢰 가능한 고유점은 380개다.
- 원인: 원자료에 시설별 실제 위치가 아닌 인근좌표·시군구 대표점이 포함되어 있고, 여러 시설이 동일 좌표를 공유한다.
- 분석 결과에 미치는 영향: 동일 위치 시설은 SGIS 경로망 요청과 주변 시설 집계가 동일하게 계산될 수 있다. 대표점·인근좌표를 포함한 순위, 상관분석, 읍면 요약은 실제 시설 위치의 차이를 반영하지 못한다.
- 해결 방법: [`docs/coordinate-correction.md`](coordinate-correction.md)의 보정표에 공식 원자료·공식 지오코더·현장조사 중 하나로 확인한 좌표만 입력한다. 보정 전에는 임의 좌표 생성, 중복점 분산, 0명 대체를 하지 않는다.
- 검증 방법: `analysis/analyze_sgis_catchment.py`의 좌표 품질 집계와 `data/analysis/validation_report.json`의 `pond_coordinate_duplicate` 검사를 재실행한다. 보정 후 SGIS를 재수집하고 보정 전후 응답 수를 비교한다.
- 근거 코드/산출물 경로: `analysis/analyze_sgis_catchment.py`, `analysis/acquire_sgis_catchment.py`, `data/analysis/coordinate_quality_audit.csv`, `data/analysis/sgis_catchment_analysis.json`, `docs/coordinate-correction.md`
- Residual risk / 남은 한계: 좌표 보정 전까지 41개 대표점과 4개 인근좌표의 시설 단위 해석은 제한된다. 중복 좌표 시설의 실제 위치가 확인되기 전에는 시설별 생활권 인구를 독립 관측치로 해석하지 않는다.

### DQ-002 — SGIS 경로망 위치 인식 실패

- Status: `Open`
- Impact: `High`
- 발견일: 2026-08-31
- 대상 데이터셋: `data/processed/population/sgis_drive_population.csv`, SGIS `serviceAreaGeometry`·`serviceAreaStatistics`
- 증상: 427개 시설 × 2개 시간대 = 854개 요청 중 399개가 `DATA_NOT_AVAILABLE`이다. 이 중 384개 행, 192개 시설은 5분·10분 모두 `unlocated` 오류를 반환했다.
- 원인: SGIS 경로망이 입력 좌표를 도로망에 연결할 위치로 인식하지 못한 경우다. 대표점·인근좌표 및 도로망 연결성의 영향을 함께 받을 수 있으며, 현재 응답만으로 어느 원인이 단독 원인인지 확정하지 않는다.
- 분석 결과에 미치는 영향: 미응답 시설을 인구 0명이나 낮은 수요로 해석할 수 없다. 응답 시설만으로 비교하면 좌표 품질과 위치 인식 가능성에 따른 선택 편향이 생긴다.
- 해결 방법: DQ-001의 좌표 보정을 먼저 수행하고, 보정된 좌표로 SGIS 5분·10분 요청을 재실행한다. 재수집 전까지 결측 상태를 유지한다.
- 검증 방법: `data/analysis/sgis_catchment_status.json`의 행 수·상태 수와 `data/analysis/sgis_catchment_analysis.json`의 진단 수치를 비교한다. `unlocated_error_rows` 및 `unlocated_error_facilities`가 감소하는지 확인한다.
- 근거 코드/산출물 경로: `analysis/acquire_sgis_catchment.py`, `analysis/analyze_sgis_catchment.py`, `docs/sgis-api.md`, `data/analysis/sgis_catchment_status.json`, `data/analysis/sgis_catchment_analysis.json`
- Residual risk / 남은 한계: 좌표를 보정해도 SGIS 경로망에 연결되지 않는 시설이 남을 수 있다. 미응답 399건 전체를 생활권 인구 분석에서 채워 넣는 것은 현재 근거로 불가능하다.

### DQ-003 — SGIS 생활권역 생성 후 인구 필드 미제공

- Status: `Open`
- Impact: `Medium`
- 발견일: 2026-08-31
- 대상 데이터셋: SGIS 생활권역 수집 결과 15행
- 증상: 399개 미응답 중 15개 행은 생활권역 geometry는 반환됐지만 인구값이 제공되지 않았다.
- 원인: SGIS 응답의 서비스 영역과 통계값 제공 여부가 분리되어 있으며, 현재 응답에는 인구 필드가 없다. 비밀보호 처리와 API 응답 조건의 구체적 내부 사유는 응답만으로 확정하지 않는다.
- 분석 결과에 미치는 영향: 서비스 영역 면적이 있다고 해서 인구가 0명이라고 볼 수 없다. 인구 기반 순위·평균·상관분석에서는 해당 행을 값이 없는 관측치로 제외한다.
- 해결 방법: 재요청 시 원 응답의 상태·필드 유무를 보존하고, 제공된 경우에만 인구값을 연결한다. 공식 격자·읍면 총계·WorldPop을 대체값으로 사용하지 않는다.
- 검증 방법: `sgis_population`과 `sgis_population_api_total`의 null 여부, `status`, `error`를 함께 검사하고 15건의 원 응답 진단 수를 재집계한다.
- 근거 코드/산출물 경로: `analysis/acquire_sgis_catchment.py`, `analysis/analyze_sgis_catchment.py`, `data/processed/population/sgis_drive_population.csv`, `docs/sgis-api.md`
- Residual risk / 남은 한계: SGIS가 같은 기준연도·좌표에 대해 이후 값을 제공할지는 보장되지 않는다. 재수집 전까지 해당 시설의 인구값은 비어 있는 상태로 남긴다.

### DQ-004 — 공식 인구격자 원자료 부재

- Status: `Open`
- Impact: `Medium`
- 발견일: 2026-08-31
- 대상 데이터셋: 공식 인구격자 Buffer 산출 대상, `data/raw/population/official_grid/`
- 증상: 100m·500m 공식 인구격자 원자료가 저장소에 확보되지 않았다. 현재 확보된 행정안전부 자료는 읍면동 집계이며, SGIS 생활권역 값은 주행시간 기반 도달 규모다.
- 원인: 공개·사용 가능한 공식 격자 파일과 인구 필드, 기준연도, 이용조건을 아직 확인하지 못했다.
- 분석 결과에 미치는 영향: 500m·1km Buffer 안의 주민등록 인구를 읍면 총계로 임의 배분하거나 SGIS 주행인구로 대체할 수 없다. 따라서 해당 Buffer 인구는 공식 격자 확보 전까지 `DATA_NOT_AVAILABLE`로 유지한다.
- 해결 방법: 공식 제공기관의 격자 geometry, 인구 필드, 기준연도, 비밀보호·라이선스 조건을 확인한 뒤 원자료를 `data/raw/population/official_grid/`에 두고 manifest에 기록한다.
- 검증 방법: 격자 CRS·geometry valid·인구 필드·기준연도·의성군 범위를 확인하고, `pond_context_analysis.py`의 격자 Intersection 결과와 `validation_report.json`을 갱신한다.
- 근거 코드/산출물 경로: `data/README.md`, `docs/methodology.md`, `data/manifests/population_sources.csv`, `analysis/pond_context_analysis.py`
- Residual risk / 남은 한계: 격자 확보 전에는 시설 주변 거주인구와 SGIS 주행인구를 하나의 인구 지표로 비교할 수 없다. WorldPop은 참고 raster일 뿐 국내 공식 주민등록 격자의 대체값으로 사용하지 않는다.

### DQ-005 — VWorld 및 기존 공간자료 snapshot·라이선스 메타데이터 미완결

- Status: `Open`
- Impact: `Medium`
- 발견일: 2026-08-31
- 대상 데이터셋: VWorld UQ164·UO601·UQ151, 기존 `uiseong_boundary.geojson`, `agricultural_areas.geojson`
- 증상: VWorld 레이어는 분석에 사용 가능하지만 manifest의 접근일·기준 snapshot 정보와 원자료 이용조건 확인이 완결되지 않았다. 행정경계·농업지역은 기존 프로젝트 자료로 사용되며 원자료 출처가 VWorld로 검증된 상태가 아니다.
- 원인: 기관별 다운로드 시점·레이어 버전·재배포 조건을 동일한 메타데이터 형식으로 확보하지 못했다.
- 분석 결과에 미치는 영향: 현재 geometry·거리·집계 결과의 수치 검증과 별개로, 동일 분석을 새 환경에서 재현하거나 결과물을 재배포할 때 원자료 버전과 이용권한을 설명하기 어렵다.
- 해결 방법: 새 snapshot을 반입할 때 provider, layer, accessed_at, reference period, source path, CRS, license URL, hash, redistribution status를 manifest에 기록한다. 기존 경계·농업자료는 실제 출처를 확인하기 전까지 `EXISTING_LOCAL_DATA_NOT_VERIFIED`로 표시한다.
- 검증 방법: `data/manifests/vworld_sources.csv`와 `data/analysis/vworld_layer_inventory.json`의 레이어·필드·CRS·feature count를 대조하고, 새 snapshot마다 파이프라인과 라이선스 검토를 다시 수행한다.
- 근거 코드/산출물 경로: `data/manifests/vworld_sources.csv`, `data/analysis/vworld_layer_inventory.json`, `data/analysis/vworld_input_status.json`, `data/README.md`
- Residual risk / 남은 한계: 원자료 이용조건 확인 전에는 VWorld 원본을 Git에 추가하거나 결과물을 원자료와 함께 재배포하지 않는다. snapshot이 바뀌면 시설 주변 집계가 달라질 수 있다.

### DQ-006 — 원자료·파생자료 인코딩 차이

- Status: `Resolved`
- Impact: `Low`
- 발견일: 2026-08-31
- 대상 데이터셋: 행정안전부 CSV와 `data/processed/` CSV·JSON·GeoJSON
- 증상: 행정안전부 원자료는 `CP949`, 파생 산출물은 UTF-8 계열로 관리된다. 인코딩을 지정하지 않으면 읍면명·필드명이 깨질 수 있다.
- 원인: 제공기관 원자료와 Python 파생 출력의 기본 인코딩이 다르다.
- 분석 결과에 미치는 영향: 잘못 읽으면 행정구역 매칭과 문자 필터가 실패할 수 있으나, 현재 처리 스크립트는 원자료 인코딩을 명시하고 파생 결과를 표준 출력 인코딩으로 저장한다.
- 해결 방법: manifest에 `CP949`를 기록하고 입력 단계에서 인코딩을 명시한다. 출력 단계는 UTF-8/UTF-8-SIG 등 파일 형식별 약속을 유지한다.
- 검증 방법: population 전처리와 통합 파이프라인을 재실행하고 18개 읍면 매칭, 427개 시설, 필수 출력 파일 존재 여부를 확인한다.
- 근거 코드/산출물 경로: `data/manifests/population_sources.csv`, `analysis/prepare_population.py`, `data/processed/population/uiseong_population.csv`, `data/analysis/validation_report.json`
- Residual risk / 남은 한계: 새 기관 CSV가 추가되면 인코딩을 다시 확인해야 하며, 터미널 표시가 깨져 보여도 파일 바이트와 실제 파싱 결과를 기준으로 판단한다.

### DQ-007 — CRS·geometry 처리 차이

- Status: `Resolved`
- Impact: `Medium`
- 발견일: 2026-08-31
- 대상 데이터셋: 못·VWorld 공간자료·SGIS 서비스 영역
- 증상: 웹 표시는 EPSG:4326, 거리·Buffer 계산은 EPSG:5174, SGIS 응답 원자료는 EPSG:5179를 사용한다. 일부 VWorld SHP에는 ring winding 경고가 발생했다.
- 원인: 기관별 제공 CRS와 분석 목적별 좌표계가 다르다. 원본 SHP의 geometry 방향도 표준화가 필요한 형태로 제공됐다.
- 분석 결과에 미치는 영향: CRS를 섞으면 거리·면적 단위가 틀릴 수 있고, 잘못된 geometry는 Clip·Intersection에 영향을 줄 수 있다.
- 해결 방법: 거리·면적 계산 전 EPSG:5174로 변환하고, 웹 출력은 EPSG:4326으로 변환한다. 입력 geometry는 처리 단계에서 유효성·방향을 점검하고 원본은 변경하지 않는다.
- 검증 방법: `validation_report.json`의 CRS, geometry valid, 경계 밖, 거리 meter, Buffer area 검사를 통과시킨다. 현재 geometry invalid 0건, 도로·시설 CRS 검증 PASS다.
- 근거 코드/산출물 경로: `analysis/prepare_vworld.py`, `analysis/pond_context_analysis.py`, `data/analysis/validation_report.json`, `data/geojson/`
- Residual risk / 남은 한계: 새 기관 레이어나 SGIS geometry를 추가할 때 CRS와 단위 확인을 생략하면 같은 이슈가 재발할 수 있다.

### DQ-008 — 기관별 기준연도·snapshot 차이

- Status: `Accepted limitation`
- Impact: `Medium`
- 발견일: 2026-08-31
- 대상 데이터셋: 행정안전부 2024-12·2025-12, SGIS 2024, VWorld 공간 레이어 snapshot
- 증상: 인구·생활권역·공간 레이어가 같은 기준시점의 자료가 아니다. 행정안전부 파생 인구는 2025년을 기본 비교시점으로 사용하고, SGIS 주행인구는 2024년 요청 결과다.
- 원인: 기관별 공개 주기와 API·다운로드 기준시점이 다르다.
- 분석 결과에 미치는 영향: 서로 다른 시점의 값을 동일 시점의 변화량이나 인과관계로 해석할 수 없다. 현재는 각 지표의 기준연도와 출처를 분리해 표기한다.
- 해결 방법: manifest와 분석 문서에 기준연도를 함께 기록하고, SGIS 값·행정 읍면 인구·VWorld 시설 집계를 별도 지표로 유지한다.
- 검증 방법: `data/manifests/*.csv`, `data/analysis/sgis_catchment_analysis.json`, 제출근거 검증 스크립트의 수치·출처 대조를 실행한다.
- 근거 코드/산출물 경로: `data/manifests/population_sources.csv`, `data/manifests/sgis_sources.csv`, `docs/sgis-api.md`, `data/analysis/submission_claims_report.json`
- Residual risk / 남은 한계: 기준연도를 완전히 통일하지 못하므로 “동일 시점의 효과” 또는 정책 시행 전후 효과로 주장하지 않는다.

### DQ-009 — 행정통계·생활권 통계·격자 Buffer의 정의 차이

- Status: `Accepted limitation`
- Impact: `Medium`
- 발견일: 2026-08-31
- 대상 데이터셋: 행정안전부 읍면 집계, SGIS 생활권역 주행인구, 공식 인구격자 Buffer 대상
- 증상: 읍면 집계는 행정구역에 귀속된 주민등록 인구이고, SGIS 값은 시설에서 5분·10분 주행으로 도달 가능한 서비스 영역의 통계값이다. 격자 Buffer 인구는 별도의 geometry 교차합산 결과여야 한다.
- 원인: 기관별 공간단위와 산출 방법이 다르며, SGIS 생활권역은 시설 간 중첩될 수 있다.
- 분석 결과에 미치는 영향: 세 값을 같은 “주변 거주인구”로 합치거나 시설 간 합산하면 중복·정의 혼동이 발생한다. SGIS `DATA_NOT_AVAILABLE`을 0명으로 볼 수 없다.
- 해결 방법: 필드명을 `pond_emd_population_context`, `sgis_drive_population_5min/10min`처럼 분리하고, 공식 격자가 없으면 Buffer 인구를 산출하지 않는다. 생활권 인구는 시설별 도달 규모로만 비교한다.
- 검증 방법: `docs/methodology.md`, `docs/sgis-catchment-analysis.md`, `docs/sgis-policy-evidence.md`의 정의와 산출물 필드를 대조하고, 제출근거 검증에서 미확보 지표의 대체 여부를 검사한다.
- 근거 코드/산출물 경로: `analysis/pond_context_analysis.py`, `analysis/analyze_sgis_catchment.py`, `data/analysis/submission_claims_report.json`, `data/README.md`
- Residual risk / 남은 한계: 행정통계와 생활권 통계의 상관은 공간단위가 다른 기술통계일 뿐이며, 인구의 총합·정책 수요의 총량으로 해석하지 않는다.

### DQ-010 — 시설 ID·필수 필드·출력 스키마

- Status: `Resolved`
- Impact: `Low`
- 발견일: 2026-08-31
- 대상 데이터셋: 427개 시설 원자료와 `data/processed/`, `data/analysis/`, `data/geojson/` 출력
- 증상: 새 snapshot을 연결할 때 시설 ID, 분류 필드, 결측 상태 필드가 서로 다른 이름으로 들어오면 join 누락이나 의미 변경이 발생할 수 있다.
- 원인: 기관별 원자료 필드명과 프로젝트 출력 schema가 다르며, 일부 원자료는 `CLSS` 등 축약 필드를 사용한다.
- 분석 결과에 미치는 영향: ID가 바뀌거나 필수 필드가 누락되면 427개 시설 보존, 공간조인, `classification_reason` 연결이 깨질 수 있다.
- 해결 방법: 정제 단계에서 프로젝트 표준 필드로 매핑하고, 원자료 필드 의미는 manifest·문서에 보존한다. 새 snapshot은 기존 schema와 비교한 후 연결한다.
- 검증 방법: 현재 `pond_id` 중복 0건, 필수 `id/capacity/geometry` null 0건, 시설 수 427건, 공간조인 누락 0건을 `validation_report.json`에서 확인한다.
- 근거 코드/산출물 경로: `analysis/validate_outputs.py`, `analysis/validate_submission_claims.py`, `data/analysis/validation_report.json`, `data/geojson/ponds_classified.geojson`
- Residual risk / 남은 한계: 새 원자료의 필드가 추가·변경되면 현재 검증만으로 의미 일치를 보장할 수 없다. snapshot 반입 시 schema diff와 표본 속성 대조를 다시 수행한다.

## Open issues / watchlist

다음 5개는 현재 수치 산출을 임의로 보완하지 않고 열린 상태로 관리한다.

- DQ-001: 41개 대표점·4개 인근좌표와 43개 중복좌표 시설의 실제 위치 확인
- DQ-002: 좌표 보정 후 SGIS `unlocated` 384행 재수집
- DQ-003: SGIS geometry는 있으나 인구값이 없는 15행 재요청·응답 조건 확인
- DQ-004: 공식 인구격자 geometry·인구 필드·기준연도·이용조건 확보
- DQ-005: VWorld 접근일·snapshot·라이선스와 기존 경계·농업지역 출처 검증

새 데이터셋이나 snapshot을 추가할 때는 먼저 이 watchlist의 재발 여부를 확인하고, 처리 결과를 해당 이슈의 `Status`, 검증 산출물, Residual risk에 반영한다. 원자료가 갱신되어도 기존 해결 이슈의 기록은 삭제하지 않는다.

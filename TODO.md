# 인구감소지역 유휴공간 정책매칭 모델 TODO

최종 확인일: 2026-09-09 KST

> 기존 VWorld 공모전 데이터 확보 항목은 아래에 이력으로 보존한다. 현재 우선순위는 전국 전수분석이 아닌 SGIS 공모전용 의성 Case Study다. 상세 방향은 [`docs/sgis-uiseong-policy-proposal-guideline.md`](docs/sgis-uiseong-policy-proposal-guideline.md)를 따른다. 이전의 전국 정책매칭 확장안은 범위 축소로 보류한다.

## NOW — 지금 공모전 제출을 위해 바로 해야 하는 작업

- 상태: 진행 중 — SGIS 의성 Case Study 제출 품질 검토
- 마지막 업데이트: 2026-08-31
- 다음 액션: 좌표·현장자료를 확인할 수 있는 항목부터 검토하고, 제출문서 수치와 산출물·manifest를 최종 대조한다.

### 제출 우선순위 요약

- [ ] SGIS 결측·좌표 보정 및 재추출
- [ ] 현장자료 기반 정책 후보 검증
- [ ] 데이터 기준연도·출처·manifest 최종 검증
- [ ] SGIS + 427개 못 정책 해석 확정
- [x] 공모전 지도·그래프 최종 제작 (`docs/submission/sgis-uiseong-submission-report.md`의 시각화 목록)
- [x] 제출 보고서 작성 (`docs/submission/sgis-uiseong-submission-report.md`, `docs/submission/sgis-uiseong-excellent-use-case-submission.docx`; 로컬 전용)
- [x] 제출 수치 자동 검증
- [x] SGIS 심사기준에 맞춘 최종 Markdown 원고 수정 및 실제 초안 포함 제출근거 65개 검증 (`docs/submission/sgis-uiseong-final-draft.md`; 로컬 전용)
- [ ] 수정 원고를 Word 제출 서식에 반영하고 본문 5쪽·별첨의 실제 렌더링 확인 (기존 DOCX는 이전 편집본)

첫 화면의 상위 작업은 제출에 직접 영향을 주는 묶음만 보여준다. 외부 자료가 필요한 세부 항목과 완료된 검증 이력은 아래 접힌 목록에서 유지한다.

<details>
<summary>NOW 상세 실행 체크리스트</summary>

### 1. SGIS 결측·좌표·정책근거 검증

- [x] `DATA_NOT_AVAILABLE` 399건은 원자료 좌표 문제와 SGIS 위치 인식·통계값 미반환 문제를 분리해 보고서에 표기
- [ ] `coordinate_correction_template.csv`에 실제 좌표 출처가 확보된 못만 입력하고 SGIS 재수집
- [ ] 대표점·중복좌표 43개 보정자료 확보 후 SGIS 재추출
- [ ] 정책 근거표 후보를 현장관리 상태·보존가치·실제 서비스 수요와 대조
- [ ] 427개 시설 ID와 연결되는 관리상태, 보존가치, 현장사진/조사일 필드 정리
- [ ] 개인정보·연락처·개인 식별정보는 제외
- [ ] 시설 ID 매칭표를 만들고 `management`, `survey_status`, `heritage_note` 필드를 명시
- [ ] 출처와 조사 기준일을 README 또는 별도 manifest에 기록
- [x] 각 유형별 표본 시설의 `classification_reason` 확인
- [x] 원자료 속성·지도와 대조
- [x] fallback 발생원인 집계
- [x] `D_PRESERVATION` 또는 기타 fallback 비율 확인

### 2. SGIS 기준·수치·출처 최종 대조

- [x] SGIS 응답의 기준연도·비밀보호·주행 네트워크·이용조건을 제출문서와 manifest에서 최종 대조
- [x] SGIS 통계가 정책 판단을 어떻게 바꾸는지 비교표 작성 (`docs/sgis-policy-comparison.md`)
- [x] 정책 검토 그룹의 427개 합계·상호배타 여부·SGIS 미확보 190개 중복 여부 검증
- [x] 결측·비밀보호·생활권 중복 처리방식 문서화
- [x] 인구 기준연도와 시설·도로 데이터 기준시점을 README에 함께 표시
- [x] 제출 전 문서에 적힌 모든 수치와 manifest를 최종 대조
- [x] 실제 VWorld 자료의 레이어·파일·의성군 범위 확인 결과와 제출문서 수치 대조
- [x] `data/analysis/validation_report.json`이 PASS인지 확인
- [x] `analysis/validate_submission_claims.py`로 제출문서의 검증 수치·산출물·미구현 주장 자동 점검
- [x] `data/analysis/submission_claims_report.json` 생성 및 통합 파이프라인 연결 상태 확인

### 3. 제출물 작성·검토

- [x] SGIS 공모전 제출용 분석 흐름과 의성 사례 작성 (`docs/submission/sgis-uiseong-submission-report.md`; 로컬 전용)
- [x] 지역 특성·수요·못 특성·접근성에서 활용 가능성으로 이어지는 해석표 작성 (`docs/sgis-policy-comparison.md`)
- [x] 청년·관광·일자리·생활지원 정책 후보의 근거 정리 — 현재 자료로 확인 가능한 청년·공동체·접근·도달 검토 가설을 정리하고, 일자리·현장수요는 추가 확인 대상으로 표시
- [ ] 정책을 먼저 정하지 않았음을 분석 흐름과 근거로 검증
- [x] SGIS 통계가 기존 의성 정책 제안에 추가한 근거 정리 (`docs/sgis-policy-comparison.md`)
- [x] 의성 통계·못·공간분석 결과의 정책 중심 지도·그래프 작성 (`analysis/figures/` 및 제출 보고서 시각화 목록)

</details>

## NEXT — NOW 완료 후 진행할 작업

- 상태: 대기 — 현장·좌표·수치 검증 완료 후 보고서 완성
- 마지막 업데이트: 2026-08-31
- 다음 액션: NOW의 후보 검토 결과를 반영해 활용 가능성 해석과 정책 제안의 연결관계를 확정한다.

### P1 — 의성 지역자원·공간분석 정리

- [ ] 도로·관광·생활 인프라와 못의 공간적 관계 중 필요한 분석만 선정
- [ ] SGIS 지역통계와 427개 못 분석 결과를 정책 근거로 해석
- [ ] 지역 수요 유형화 규칙과 `classification_reason` 근거 정의
- [ ] 선정 지표의 기준연도와 공간단위 통일

### P2 — 정책 접근 프레임·보고서 보완

- [ ] NOW에서 확정한 해석표와 정책 후보를 최종 제출문서 형식에 맞게 편집
- [ ] NOW의 현장·좌표 검토 결과를 반영해 보고서 서술을 갱신

## BLOCKED — 외부 데이터·좌표·라이선스 등으로 현재 진행이 막힌 작업

- 상태: 부분 차단 — 자료가 없거나 외부 확인이 필요한 항목
- 마지막 업데이트: 2026-08-31
- 다음 액션: 실제 원자료·공식 링크·현장조사 결과가 확보된 항목만 입력하고, 확보 전에는 `DATA_NOT_AVAILABLE`을 유지한다.

### 1. 국내 공식 인구 격자 데이터 — Buffer 인구 산출용

- [ ] 읍·면 총계가 아닌 실제 격자 단위 인구자료 확보 여부 확인
- [ ] 국내 공식 인구 격자자료 확보 및 WorldPop과 별도 기준으로 관리
- [ ] 가능하면 100m 또는 500m 격자, 기준연도, 인구·청년·고령 필드가 있는 자료 사용
- [ ] 확보 시 `data/raw/population/`에 보관하고 `pond_context_analysis.py`에 격자 Intersection 추가

비고: 국내 공식 주민등록 격자와 기준·모형이 다르므로 현재 공식 Buffer 인구값은 계속 `DATA_NOT_AVAILABLE`로 둔다. 읍·면 총계나 SGIS 생활권역 값을 Buffer 안의 인구로 임의 배분하지 않는다.

### 2. 좌표·현장조사 자료

- [ ] `coordinate_correction_template.csv`의 보정값에 VWorld·공공데이터·현장조사 등 실제 출처 기록
- [ ] `confidence`를 `HIGH`, `MEDIUM`, `LOW` 중 하나로 기록
- [ ] 좌표를 임의 추정하지 않고, 원자료·공식 지오코더·현장조사 중 하나를 근거로 기록
- [ ] 보정 좌표 입력 후 기존 분석 결과와 비교

현재 `data/processed/ponds.csv`에는 `CLSS=시군구 좌표` 41개, `인근좌표` 4개, 동일 주소·좌표가 확인된 406·415번이 있어 실제 좌표 확인 전까지 SGIS 순위·상관·읍면 요약에서 제외한다.

### 3. VWorld 최종 이용조건

- [ ] VWorld 원자료의 최종 라이선스·재배포 조건 확인
- [ ] 도로·생활시설 원자료를 GitHub에 올릴 수 있는지 이용조건 확인
- [ ] VWorld 레이어명, 다운로드일, 제공기관, 이용조건을 `data/manifests/vworld_sources.csv`에 입력
- [ ] 원자료 파일과 제출물에 적용되는 출처표시·상업적 이용금지·변경금지 조건 확인

### 4. SGIS 지역통계 API의 의성군 세부지표

공식 SGIS 데이터 API의 인구·연령·가구·주택·사업체 지표는 인증은 되지만 의성군 코드 `47730`에서 현재 분석에 사용할 응답이 확보되지 않았다. 따라서 실제 `AVAILABLE` 응답이 확인되기 전에는 MOIS 자료를 SGIS 지역통계로 오표기하지 않는다.

- [ ] 의성군 코드 `47730`에서 SGIS 인구·연령·가구·주택·사업체 지표의 재제공 여부 확인
- [ ] SGIS 지표가 `AVAILABLE`로 바뀌면 기준연도·공간단위·결측처리 기준을 재검토

## LATER — 공모전 이후 확장 또는 조건부 아이디어

- 상태: 보류 — 현재 제출 범위 밖이거나 조건부 적용 항목
- 마지막 업데이트: 2026-08-31
- 다음 액션: 공모전 제출본 안정화 후 자료 범위·라이선스·정답라벨을 다시 확인하고 선택적으로 진행한다.

### 1. 전국 확장·정책매칭 모델

- [ ] 전국 전수분석·완성형 전국 추천시스템 구축
- [ ] 다른 인구감소지역에 즉시 적용 가능한 확장형 데이터·정책매칭 구조 구축
- [ ] 전국 즉시 적용이 아니라 다른 인구감소지역에 적용 가능한 접근방향으로 표현
- [ ] 확장 가능한 diffusion kit 구축

### 2. Web GIS·API·DB

- [ ] Web GIS·API·DB는 공모전 이후 확장 항목으로 유지
- [ ] Flask 기반 VWorld 실시간 API 프록시
- [ ] 실시간 VWorld API Web GIS 연동
- [ ] 신규 결과 GeoJSON을 기존 Leaflet 레이어와 Popup에 연결
- [ ] PostgreSQL + PostGIS 구축과 재현 가능한 import/seed 과정 검토

### 3. WorldPop 참고자료 확장

- [x] WorldPop Global2 한국 100m 인구 raster 2020 constrained 확보
- [x] 원자료 보관: `data/raw/population/worldpop/kor_pop_2020_CN_100m_R2025A_v1.tif`
- [x] 다운로드 재현 스크립트: `python analysis/acquire_worldpop.py`
- [x] 출처·접근일·SHA-256·라이선스 링크를 `data/manifests/worldpop_sources.csv`에 기록

비고: WorldPop은 약 100m(3 arc-second) 격자별 추정 인구수다. 국내 주민등록 인구와 산출모형·기준시점이 다르므로 공모전의 공식 인구값을 대체하지 않고, 인구분포 비교·Buffer 참고·시각화용으로만 사용한다. 원자료 라이선스는 [WorldPop licence](https://www.worldpop.org/data/licence.txt)를 확인한다.

### 4. 생활SOC 2020 자료를 수요·입지 보조지표로 사용

대상 파일: `vworld/gb_r032.zip`, `vworld/gb_r033.zip`

- [ ] `gb_r032`의 `FAC_TYP`, `FAC_NM`, `GRADE_TYP`, `GRADE`, `GRID_ID` 의미와 등급 방향 확인
- [ ] `gb_r033`의 시·군·구별 `GRADE`가 어떤 입지분석 결과인지 정의서로 재확인
- [ ] 의성군을 포함하는 동일 자료의 최신/전국판 또는 의성군 Clip 자료 확보
- [ ] EPSG:4326을 EPSG:5174로 변환한 뒤 500m·1km Buffer와 Intersection
- [ ] `socs_grade_mean_500m`, `socs_high_grade_grid_count_1km`, `socs_context_status` 같은 별도 필드로 저장
- [ ] 시설 개수(`facility_count`)나 공공시설 원자료로 오인하지 않고, 생활SOC 수요·유인력·입지등급 보조변수로만 사용

현재 판단: **조건부 가능**. 정의서상 생활SOC 생활문화센터군의 유인력·수요도/입지분석 격자·Polygon 자료이지만, 현재 파일의 공간범위는 의성군을 포함하지 않아 그대로 사용할 수 없다. 의성군 범위 자료를 추가로 확보할 때만 적용한다.

### 5. 교통문화지수의 추가 활용

대상 파일: `vworld/T_W_BASE_ART_CULT_IDX.zip`, `vworld/T_W_BASE_TRF_CULT_IDX.zip`

- [x] TXT를 UTF-8-SIG, `|` 구분자로 읽고 정의서의 컬럼명을 적용
- [x] `JIJACE_CD = 47730`(경북 의성군) 레코드만 추출
- [x] `T_W_BASE_ART_CULT_IDX`: 2014~2024 연도별 운전행태 관련 지표와 기타 문화지수 항목 확인
- [x] `T_W_BASE_TRF_CULT_IDX`: 2017~2024 연도별 운전행태·교통안전·보행·교통약자·문화 점수 및 순위 확인
- [x] 최근 연도 값과 기준연도를 `data/analysis/traffic_culture_context.json`에 저장
- [x] 공모전 `competition_metrics.json`에 군 단위 배경지표 상태 기록
- [x] 시설별 500m·1km 접근성이나 도로거리로 복제하지 않고 `uiseong_county_context`로 명확히 표시
- [x] 출처·작성기관·연도·컬럼정의를 별도 manifest에 기록
- [ ] 생활SOC 의성군 자료 확보 시 `B_ECO_EDUCATION`·`C_COMMUNITY` 분류의 보조 근거로 검토
- [ ] 교통문화지수는 `classification_reason`에 직접 점수판정으로 넣기보다 “의성군 단위 배경지표”로 별도 표시
- [ ] 임의 가중치를 새로 만들지 않고 변수분포·결측·연도 차이를 먼저 확인
- [ ] 2020 생활SOC와 2024 교통문화지수를 결합할 경우 기준연도 차이를 결과 설명에 명시
- [ ] 원자료 라이선스와 공모전 제출물 포함 가능 여부 확인

현재 판단: **적용 가능**. 의성군 코드 `47730` 레코드가 존재하며, 2024년 값까지 확인된다. 다만 공간해상도가 시·군·구 단위라서 개별 못의 접근성 우열이나 생활시설 개수를 설명하는 직접 변수로 사용하지 않고, 의성군 전체 교통·문화 환경의 참고지표로만 사용한다.

### 6. 머신러닝·정책 우선순위 점수

- [ ] Random Forest GeoAI 분류모델 구현
- [ ] `classification_model.pkl` 생성
- [ ] 누가 427개의 A~E 정답을 부여했는지 정의
- [ ] 라벨 기준·학습/검증 데이터 누수·결측값·class imbalance 확인
- [ ] confusion matrix, per-class precision/recall/F1, macro/weighted F1, feature importance, random seed, split 방법, model version 산출
- [ ] 정책 우선순위 0~100 점수 구현
- [ ] 각 지표의 방향성·결측 처리·정규화·가중치 근거 기록
- [ ] 기본·접근성 강조·보전 강조·청년활동 강조 시나리오와 민감도 분석 수행
- [ ] `top50`을 행정적으로 정해진 기준이 아니라 “정책 우선후보 예시”로 표현

## DONE — 이미 완료된 핵심 작업 요약

- 상태: 완료 — 현재 제출본에서 재사용 가능한 핵심 분석·자료·문서
- 마지막 업데이트: 2026-08-31
- 다음 액션: 완료된 수치는 NOW의 최종 대조에서 다시 확인하고, 새 값으로 임의 변경하지 않는다.

### 1. 공모전 문제정의·범위

- [x] 인구감소지역 유휴자원 문제와 의성 Case Study 역할 확정
- [x] 전국 전수분석·완성형 전국 추천시스템을 범위에서 제외
- [x] 의성 427개 전통 못을 실제 분석 중심 Case Study로 분리 표기
- [x] 기존 427개 못 데이터와 현장조사·선행성과의 재사용 범위 정의
- [x] SGIS 정책판단용 최소 지표 목록 확정
- [x] 인구·청년·고령·가구·주택·사업체 중 필요한 지표를 검토하고 실제 확보 지표를 선정
- [x] 실제 확보된 SGIS 생활권역 5분·10분 인구를 핵심 수요 지표로 선정
- [x] SGIS 공식 지역통계 endpoint(인구·연령·가구·주택·사업체)의 의성군 `47730` 가용성 점검
- [x] SGIS 5·10분 도달인구와 읍·면 인구구조·주변환경을 연결한 정책 근거표 생성
- [x] SGIS 10분 인구 확보 시설만 정책 검토 후보에 포함하도록 기준 정리
- [x] 시설별 관리상태·보존가치·현장조사 입력 템플릿 생성

### 2. 인구 자료·행정통계

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

### 3. SGIS 생활권역 주행시간 인구

- [x] SGIS 생활권역에서 5분·10분 주행권역 인구의 응답 추출 가능 여부 확인
- [x] SGIS API 인증 및 427개 시설 반복 처리
- [x] SGIS 자료제공 또는 허용된 API/응답 방식으로 427개 시설 반복 처리가 가능한지 확인
- [x] `sgis_drive_population_5min`, `sgis_drive_population_10min`으로 별도 저장
- [x] 공식 인구격자 Buffer 값이나 행정안전부 주민등록 인구로 혼용하지 않음
- [x] SGIS 비밀보호 처리와 결측 응답을 별도 상태로 보존

현재 결과: 427개 못 × 2개 시간대, 총 854건 중 `AVAILABLE` 455건, `DATA_NOT_AVAILABLE` 399건. 미응답 399건은 위치 인식 실패 384건과 생활권역은 생성됐으나 인구 필드가 없는 15건으로 분리해 분석했다. 결과는 `data/processed/population/sgis_drive_population.csv`, `data/analysis/sgis_catchment_analysis.json`, `data/analysis/sgis_indicator_availability.json`에 기록했다.

### 4. VWorld 도로·생활·공공·문화·관광시설

- [x] VWorld 계정으로 로그인 후 도로 SHP 다운로드
- [x] 파일명: `C_UQ151.zip`
- [ ] 공식 데이터 페이지: [국토교통부\_도로(현황)](https://www.vworld.kr/dtmk/dtmk_ntads_s002.do?dsId=30074)
- [x] 다운로드 파일을 기존 `vworld/`에 보관
- [x] 압축 해제 후 SHP·SHX·DBF·PRJ가 모두 있는지 확인
- [x] 원본 좌표계가 EPSG:5174인지 확인
- [x] 전국 원본을 의성군 경계로 Clip하여 `data/processed/roads/uiseong_roads.gpkg` 생성
- [x] 도로 데이터 확보 후 파이프라인에서 427개 최근접거리 계산
- [x] VWorld `LSMD_CONT_UQ164_5174_경북.zip` 선택 — 공공·교육·문화·안전시설 Polygon
- [x] VWorld `LSMD_CONT_UO601_5174_경북.zip` 선택 — 관광지·관광특구 Polygon
- [x] 의성군 코드 `47730` 선별 및 EPSG:5174 변환
- [x] 의성군 경계 Clip 결과를 `data/processed/facilities/uiseong_facilities.gpkg`로 저장
- [x] `facility_count_500m`, `facility_count_1000m` 계산
- [x] 전체 파일 분류·제외사유를 `data/analysis/vworld_layer_inventory.json`에 기록
- [x] 실제 VWorld 자료의 레이어·파일·의성군 범위 확인
- [x] VWorld 시설 CRS, geometry valid, 의성군 경계 밖 데이터 검증
- [x] 도로 거리 단위가 meter인지 확인
- [x] 500m·1km 면적 단위가 m²/ha인지 확인

현재 처리 결과: VWorld 시설 68개(UQ164 67개 + UO601 1개). `facility_category`는 관광·문화·교육·보건·공공안전·체육·기타 공공시설로 구분했다.

참고: 공공데이터포털 설명상 도로 데이터는 무료 SHP이며 VWorld 다운로드 페이지로 연결되지만, 로그인 후 다운로드가 필요하다. 건축물·하천·토지 자료는 시설 Point나 도로 중심선의 대체재로 사용하지 않았다. UQ151 최근접거리는 도로 네트워크 이동거리나 주행시간이 아닌 EPSG:5174 미터 단위 유클리드 최근접거리다.

### 5. 교통문화지수·기존 분석 자동화

- [x] 교통문화지수 의성군 시군구 배경지표 추출·결과파일 연결 완료
- [x] `data/analysis/traffic_culture_context.json` 및 `competition_metrics.json` 연결
- [x] 접근성·활용유형 관련 분석 산출물 생성
- [x] CSV / JSON / GeoJSON / GPKG / PNG 산출물 생성
- [x] `data/analysis/validation_report.json`이 PASS인지 확인
- [x] `analysis/validate_submission_claims.py`로 제출근거 자동 점검 코드 생성
- [x] `data/analysis/submission_claims_report.json` 생성 및 통합 파이프라인 연결
- [x] `python analysis/run_competition_pipeline.py` 실행 구조 확인

### 기존 상태·판단 기록 보존

기존 기록: 행정안전부 인구는 공공데이터 원자료 확보·처리 완료. VWorld UQ164·UO601 시설 원자료는 의성군 68개를 처리했고, UQ151 도로 공간파일은 확보하여 파이프라인 연결 중이다.

- 인구 자료: 확보 완료, 분석 연결 완료
- 인구 원자료 보관: `data/raw/population/`(대용량 원본은 Git 추적 제외)
- 기존 농업지역: 기존 프로젝트 자료로 계산 가능하지만 VWorld 출처는 미확인
- VWorld 도로: 계정 로그인 및 대용량 SHP 다운로드 필요
- VWorld 생활시설: UQ164·UO601 확보·Clip·시설 Buffer 계산 완료
- 인구 Buffer: 국내 공식 격자자료 분석 연결 전이므로 공식 인구값은 `DATA_NOT_AVAILABLE`; WorldPop은 참고용 확보 완료
- 생활SOC 2020: 의성군 범위 자료 확보 전까지 아이디어로 보류
- 교통문화지수: 의성군 시군구 배경지표 추출·결과파일 연결 완료
- React/API/DB: 이번 데이터 확보 단계에서는 미적용

### 참고자료·출처 운영 원칙

- 상태: 유지 — 자료를 추가할 때 적용하는 출처·재현성 원칙
- 마지막 업데이트: 2026-08-31
- 다음 액션: NOW의 최종 대조 시 각 원자료의 manifest와 제출문서 수치를 함께 확인한다.

본 분석은 아래 순서로 자료를 채운다.

1. **VWorld 원자료**: 도로·생활SOC·공공·문화·관광시설의 1순위
2. **공공데이터 공식 원자료**: 인구·행정경계·시설 보완 자료의 2순위
3. **수동 다운로드 자료**: VWorld 로그인이나 대용량 파일 문제로 자동 확보가 안 될 때 공식 링크에서 직접 자료
4. **OSM·WorldPop**: 참고·교차검증·분포 시각화용. VWorld 또는 국내 공식 공공데이터를 확보한 것으로 간주하지 않음

원본 파일은 Git에 추가하지 않고, 출처·기준시점·SHA-256·로컬 경로·처리 결과를 `data/manifests/`에 기록한다. `data/raw/`와 루트 `vworld/` 원자료는 `.gitignore` 대상이며, 새 clone에서 원본을 다시 준비해야 한다.

# 데이터 디렉터리 안내

이 디렉터리는 원본(raw), 정제(processed), 분석 결과(analysis), 지도 출력(geojson), 출처 기록(manifests)을 분리해 관리한다.

## raw 데이터와 Git

`data/raw/`는 다운로드 원본과 대용량 raster·압축파일을 보관하는 로컬 작업공간이다. 원본 데이터는 파일 크기, 제공기관의 이용·재배포 조건, 개인정보·공공데이터 라이선스 확인 필요성 때문에 `.gitignore`로 Git 추적에서 제외한다. 따라서 새 clone에는 `data/raw/` 파일이 없어도 정상이며, 원본의 출처·기준시점·SHA-256·로컬 경로는 `data/manifests/`에 남긴다. 이 저장소에는 기존 VWorld 원자료가 별도 루트 폴더 `vworld/`에 이미 있으므로 이를 `data/raw/vworld/`로 중복 복사하지 않는다.

## 원본 데이터 위치와 출처

### VWorld

이 저장소에 이미 있는 VWorld 원본은 다음 위치에 보존한다.

```text
vworld/
```

현재 사용·검토 대상은 다음과 같다.

- `LSMD_CONT_UQ164_5174_경북.zip`: 공공·생활·문화·교육·안전시설 Polygon
- `LSMD_CONT_UO601_5174_경북.zip`: 관광지·관광특구 Polygon
- `C_UQ151.zip`: 도시계획시설 도로 현황 SHP. 의성군 Clip 후 최근접거리·Buffer 도로 geometry 길이에 사용
- `gb_r032.zip`, `gb_r033.zip`: 생활SOC 2020 참고자료. 현재 파일은 의성군 범위 밖이라 분석에 사용하지 않음
- `T_W_BASE_ART_CULT_IDX.zip`, `T_W_BASE_TRF_CULT_IDX.zip`: 교통문화지수 비공간 통계
- 기타 HWP/XLS/XLSX: 테이블 정의서·제출 양식·참조 문서

제공기관은 VWorld이며, 레이어·처리 상태·CRS·원본 경로는 `data/manifests/vworld_sources.csv`와 `data/analysis/vworld_layer_inventory.json`에서 확인한다. 공식 도로 자료는 [VWorld 국토교통부 도로(현황)](https://www.vworld.kr/dtmk/dtmk_ntads_s002.do?dsId=30074)에서 수동 다운로드한다.

### Population

행정안전부 주민등록 연령별 인구 원본은 다음 위치에 둔다.

```text
data/raw/population/
```

출처는 [주민등록 인구통계 연령별 인구현황](https://jumin.mois.go.kr/ageStatMonth.do)이며, 2024년 12월·2025년 12월 읍·면·동 집계자료를 사용한다. 기준은 의성군 코드 `4773`, 청년 만 19~39세, 고령 만 65세 이상이다. 출처와 기준시점은 `data/manifests/population_sources.csv`에 기록한다.

WorldPop 한국 100m raster는 참고자료로 다음 위치에 둔다.

```text
data/raw/population/worldpop/
```

WorldPop은 국내 주민등록 인구를 대체하지 않으며, 출처·라이선스·해시는 `data/manifests/worldpop_sources.csv`에서 관리한다.

## 필요한 디렉터리 구조

```text
data/
├─ README.md
├─ raw/                         # 로컬 원본, Git 제외
│  └─ population/
├─ manifests/                   # 출처·기준시점·재현 정보
├─ processed/                   # 정제·변환 데이터
│  ├─ facilities/
│  └─ population/
├─ analysis/                    # JSON·CSV 분석 결과
└─ geojson/                     # 지도용 GeoJSON
```

## 분석 스크립트 실행 순서

저장소 루트에서 실행한다.

```bash
python analysis/acquire_population.py       # 필요 시 인구 원본 다운로드
python analysis/acquire_worldpop.py         # 필요 시 WorldPop 참고 raster 다운로드
python analysis/check_sgis_indicators.py   # 의성군 SGIS 지역통계 endpoint 가용성 점검
python analysis/acquire_sgis_catchment.py  # SGIS 5·10분 생활권역 인구 수집(.env 필요)
python analysis/run_competition_pipeline.py
```

통합 파이프라인은 인구 전처리, VWorld 레이어 분류·처리, 인구 분석, 접근성, 시설·농업지역 Buffer, 교통문화지수, 활용유형 분류, 공모전 출력, 그림 생성, 검증 순서로 실행한다. 원본이 없을 때는 임의값을 만들지 않고 해당 지표를 `DATA_NOT_AVAILABLE`로 기록한다.

## 생성 결과

- `data/processed/population/uiseong_population.csv`: 읍·면별 인구·청년·고령 정제자료
- `data/processed/facilities/uiseong_facilities.gpkg`: VWorld UQ164·UO601에서 추출한 의성군 시설자료
- `data/analysis/`: population, context, accessibility, classification, traffic/culture, VWorld inventory, validation 결과
- `data/analysis/sgis_indicator_availability.json`: SGIS 지역통계 endpoint별 의성군 가용성 점검 결과
- `data/analysis/sgis_catchment_status.json`: SGIS 생활권역 수집 건수와 결측 상태
- `data/analysis/sgis_policy_evidence.csv/json`: SGIS 도달인구와 기존 의성 자료를 연결한 비가중 정책 근거표
- `data/analysis/policy_candidate_review_template.csv`: SGIS 근거 후보의 관리상태·보존가치·현장조사 수동 입력표
- `data/analysis/competition/`: 공모전 제출·검토용 요약 JSON
- `data/geojson/`: 시설·인구·Buffer·분류 지도 출력
- `analysis/figures/`: 자동 생성 PNG 그림

## 새 clone 환경에서 다시 준비하기

1. 저장소를 clone한다.
2. 기존 `vworld/`에 VWorld에서 수동 다운로드한 원본과 정의서를 보존한다. 새 VWorld 원본도 이 저장소의 기존 위치 정책에 따라 `vworld/`에 둔다.
3. `data/raw/population/`에 행정안전부 인구 CSV를 넣는다.
4. 필요하면 `data/raw/population/worldpop/`에 WorldPop raster를 다시 다운로드한다.
5. SGIS를 재수집하려면 `.env.example`을 참고해 루트 `.env`에 발급받은 인증값을 넣는다. `.env`는 Git에 추가하지 않는다.
6. 다운로드일, 기준연도, CRS, 라이선스, 파일 해시를 해당 manifest에 기록한다.
7. 저장소 루트에서 SGIS 점검·수집 후 `python analysis/run_competition_pipeline.py`를 실행한다.

원본 파일을 Git에 추가하지 않아도 정제 결과와 분석 결과는 스크립트로 재생성할 수 있다. 현재 UQ151 도로 원본은 `vworld/C_UQ151.zip`에 있으며, 정제 결과는 `data/processed/roads/uiseong_roads.gpkg`에 생성된다.

## 공식 인구격자 입력과 Buffer 계산

공식 인구격자를 확보하면 다음 위치에 둔다.

```text
data/raw/population/official_grid/
```

지원 형식은 GeoPackage, Shapefile, GeoJSON이며, 파일에는 공간 geometry와 총인구 필드(`population`, `total_population`, `tot_ppltn` 등)가 있어야 한다. 청년·고령 인구 필드는 선택사항이다. `analysis/pond_context_analysis.py`는 셀과 500m·1km Buffer의 교차면적 비율을 인구수에 곱해 합산하고, `official_population_500m`, `official_population_1km` 및 계산방법을 기록한다. 읍·면 총계만 있는 CSV는 격자자료로 취급하지 않는다.

공식 격자가 없으면 해당 Buffer 인구는 임의 배분하지 않고 `DATA_NOT_AVAILABLE`로 유지한다. SGIS 생활권역 5분·10분 인구는 이 계산값과 다른 서비스 산출지표이므로 `sgis_drive_population_5min`, `sgis_drive_population_10min`처럼 별도 관리해야 한다.

## SGIS 생활권역 결측 처리

SGIS 5분·10분 생활권역 인구는 시설별 도달 규모를 나타내는 분석 지표다. 현재 427개 못에 대해 854개 시간대 조합을 점검했고 455개가 인구값을 반환했다. 나머지 399개는 위치 인식 실패 또는 생활권역은 생성됐으나 인구 필드가 없는 경우이므로 결측으로 남긴다. 이 값을 공식 인구격자, 읍·면 총계, WorldPop으로 대체하지 않는다.

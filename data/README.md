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
- `LSMD_CONT_UQ151*.zip`: 도로 공간자료가 확보되면 사용
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
python analysis/run_competition_pipeline.py
```

통합 파이프라인은 인구 전처리, VWorld 레이어 분류·처리, 인구 분석, 접근성, 시설·농업지역 Buffer, 교통문화지수, 활용유형 분류, 공모전 출력, 그림 생성, 검증 순서로 실행한다. 원본이 없을 때는 임의값을 만들지 않고 해당 지표를 `DATA_NOT_AVAILABLE`로 기록한다.

## 생성 결과

- `data/processed/population/uiseong_population.csv`: 읍·면별 인구·청년·고령 정제자료
- `data/processed/facilities/uiseong_facilities.gpkg`: VWorld UQ164·UO601에서 추출한 의성군 시설자료
- `data/analysis/`: population, context, accessibility, classification, traffic/culture, VWorld inventory, validation 결과
- `data/analysis/competition/`: 공모전 제출·검토용 요약 JSON
- `data/geojson/`: 시설·인구·Buffer·분류 지도 출력
- `analysis/figures/`: 자동 생성 PNG 그림

## 새 clone 환경에서 다시 준비하기

1. 저장소를 clone한다.
2. 기존 `vworld/`에 VWorld에서 수동 다운로드한 원본과 정의서를 보존한다. 새 VWorld 원본도 이 저장소의 기존 위치 정책에 따라 `vworld/`에 둔다.
3. `data/raw/population/`에 행정안전부 인구 CSV를 넣는다.
4. 필요하면 `data/raw/population/worldpop/`에 WorldPop raster를 다시 다운로드한다.
5. 다운로드일, 기준연도, CRS, 라이선스, 파일 해시를 해당 manifest에 기록한다.
6. 저장소 루트에서 `python analysis/run_competition_pipeline.py`를 실행한다.

원본 파일을 Git에 추가하지 않아도 정제 결과와 분석 결과는 스크립트로 재생성할 수 있다. VWorld 도로 원본이 없으면 도로 거리·접근성은 `DATA_NOT_AVAILABLE` 상태로 유지된다.

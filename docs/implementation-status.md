# 개발지침 구현 점검표

점검일: 2026-08-30

## 결론

핵심 Python 분석 파이프라인과 공모전 결과파일은 구현되어 있다. 현재 VWorld 시설 원자료(UQ164·UO601)는 의성군 범위 68개를 처리했고, 교통문화지수는 의성군 전체 배경지표로 연결했다. VWorld 도로 원자료와 국내 공식 인구격자만 미확보 상태다.

## 항목별 점검

| 지침 항목 | 상태 | 근거·비고 |
| --- | --- | --- |
| 기존 696→427 시설 분석 보존 | PASS | 기존 `analysis/advanced_analysis.py`, `data/analysis/competition/competition_metrics.json`에 legacy 수치 보존 |
| 임의 데이터 생성 금지 | PASS | 원자료 미확보 지표는 `DATA_NOT_AVAILABLE` 처리 |
| 인구 원자료 | PASS | 행정안전부 2024·2025년 12월 읍·면 연령별 CSV, 18개 읍·면, 청년 만 19~39세, 고령 만 65세 이상 |
| 인구 지도·요약 | PASS | `population_summary.json`, `population_by_emd.geojson` 생성 |
| VWorld manifest | PARTIAL | `data/manifests/vworld_sources.csv`에 UQ164·UO601 시설 68개 `AVAILABLE`, UQ151 도로 `DATA_NOT_AVAILABLE` 기록 |
| 도로 접근성 | PARTIAL | 모듈·결과 구조는 있으나 도로 원자료가 없어 실제 거리값은 미산출 |
| 읍·면 인구 Context | PASS | `pond_emd_population_context`로 별도 표시. Buffer 정확 인구로 오인하지 않음 |
| 100m 격자 인구 | PARTIAL | WorldPop 2020 100m 참고 raster 확보. 공식 국내 인구격자나 Buffer Intersection 연결은 미완료 |
| 생활·문화·관광시설 | PASS WITH LIMITATION | VWorld UQ164·UO601에서 의성군 시설 68개 처리. 도로는 별도 미확보 |
| 농업지역 Buffer | PASS | 기존 분석자료로 500m·1km Intersection 및 면적 산출 |
| 활용유형 분류 | PASS | 5개 유형, 분류근거, 변수분포, summary 생성 |
| 결과 JSON·GeoJSON | PASS | `data/analysis/competition/`, `data/geojson/` 산출물 생성 |
| 그림 자동생성 | PASS | `analysis/figures/`에 10종 생성 |
| Web GIS 기존 기능 보존 | PASS | 기존 루트 Leaflet 화면과 정적 JSON loading 경로 유지 |
| Web GIS 신규 레이어 | PARTIAL | 공모전 분석 GeoJSON은 생성됐지만 루트 지도에 신규 레이어·Popup을 아직 연결하지 않음 |
| 검증 | PASS WITH WARNINGS | `validation_report.json` PASS. 좌표 중복 41건 WARN, 도로 거리 단위는 원자료 미확보로 `DATA_NOT_AVAILABLE` |
| 재현 실행 | PASS | `python analysis/run_competition_pipeline.py` |
| 교통문화지수 배경지표 | PASS | 의성군 `47730` 추출, 2024년까지 결과 JSON·CSV·manifest·competition metrics 연결 |
| README | PASS | 공모전 분석 섹션·VWorld 실제 처리 상태·출처 미확정 원칙·TODO 링크 반영 |

## 이번 작업에서 추가한 문서·자료

- 원문 개발지침: [`vworld-competition-development-guideline.md`](vworld-competition-development-guideline.md)
- 별도 작업목록: [`../TODO.md`](../TODO.md)
- WorldPop 다운로드 스크립트: [`../analysis/acquire_worldpop.py`](../analysis/acquire_worldpop.py)
- WorldPop 출처 manifest: [`../data/manifests/worldpop_sources.csv`](../data/manifests/worldpop_sources.csv)
- 교통문화지수 결과: [`../data/analysis/traffic_culture_context.json`](../data/analysis/traffic_culture_context.json)
- VWorld 전체 파일 재분류: [`../data/analysis/vworld_layer_inventory.json`](../data/analysis/vworld_layer_inventory.json)

## 다음 완료 조건

1. VWorld 도로 SHP를 수동 확보하고 기존 원자료 위치인 `vworld/`에 저장
2. 도로 GPKG를 생성하고 427개 접근성·도로 길이 Buffer를 재실행
3. 각 원자료의 레이어명·CRS·라이선스·획득일을 manifest에 입력
4. 국내 공식 격자 인구가 확보되면 WorldPop과 구분하여 Buffer 인구를 계산
5. 신규 결과 GeoJSON을 기존 Leaflet 레이어와 Popup에 연결

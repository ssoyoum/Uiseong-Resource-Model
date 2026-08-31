# 시설 좌표 보정 절차

현재 `data/processed/ponds.csv`의 `CLSS=시군구 좌표` 41개, `인근좌표` 4개, 동일 주소·좌표가 확인된 406·415번을 검토 대상으로 분리했다.

## 입력 방법

`data/analysis/coordinate_correction_template.csv`에서 실제 시설 위치를 확인한 뒤 다음 필드 중 하나의 좌표쌍을 입력한다.

- `corrected_x_epsg5174`, `corrected_y_epsg5174`: 분석용 좌표계 EPSG:5174의 미터 좌표
- `corrected_lat_wgs84`, `corrected_lng_wgs84`: 위도·경도 좌표
- `correction_source`: VWorld·공공데이터·현장조사 등 실제 출처
- `confidence`: `HIGH`, `MEDIUM`, `LOW`

좌표를 임의 추정하지 말고, 원자료·공식 지오코더·현장조사 중 하나를 근거로 기록한다. 보정 좌표를 입력하면 SGIS 주행인구 추출을 다시 실행하고, 기존 분석 결과와 비교한다.

현재 템플릿은 보정값이 비어 있으므로 기존 `ponds.geojson`이나 SGIS 결과를 자동으로 변경하지 않는다.

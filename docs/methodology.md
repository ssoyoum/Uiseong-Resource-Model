# 공모전 분석 방법론 및 데이터 한계

## 원칙

- 원자료가 확보되지 않은 지표는 임의의 값이나 simulated data를 만들지 않고 `DATA_NOT_AVAILABLE`로 기록한다.
- 웹 표시 좌표계는 `EPSG:4326`, 거리·Buffer·면적 계산은 `EPSG:5174`를 사용한다.
- 기존 696개 원자료와 경계 내부 427개 시설 분석 결과는 삭제하거나 재해석하지 않는다.
- `Spearman ρ=0.219`는 약한 관계로만 기록하며 인과관계로 표현하지 않는다.

## 현재 구현된 산출

- 기존 `data/geojson/agricultural_areas.geojson`를 이용해 시설별 500m·1km 농업지역 Intersection을 계산한다.
- VWorld UQ164·UO601에서 의성군 시설 68개를 확보하여 `facility_count_500m`, `facility_count_1000m`을 계산한다. 도로 원자료는 아직 없어 최근접거리와 도로 길이는 결측 상태로 남긴다.
- 읍·면 단위 인구통계만 확보되는 경우에도 읍·면 총계를 Buffer 내부 인구로 배분하지 않는다. 별도 격자 인구가 확보될 때만 Buffer 합산을 추가한다.

## 활용유형 분류

임의의 0~100 종합점수나 가중치를 사용하지 않는다. 충분한 입력이 확보된 경우에만 다음 규칙을 적용한다.

1. 관리상태가 불량으로 기록되면 `E_MANAGEMENT_PRIORITY`
2. 도로 300m 이내이고 1km 생활시설이 존재하면 `A_CULTURE_TOURISM`
3. 1km 농업지역 비율 상위 25%이고 도로 500m 초과이면 `B_ECO_EDUCATION`
4. 주변 고령인구와 도로 접근성이 함께 확인되면 `C_COMMUNITY`
5. 위 근거가 없거나 필수 변수가 결측이면 `D_PRESERVATION`

마지막 규칙은 정책 판정이 아니라, 현재 자료만으로 활동형을 단정하지 않기 위한 보수적 fallback이다. 각 시설에는 `classification_reason`를 저장한다.

## VWorld 출처 관리

`data/manifests/vworld_sources.csv`에 데이터명, 제공기관, 레이어/API, 획득일, 원본 CRS, 목적, 가공법, 이용조건을 기록한다. 현재 VWorld UQ164·UO601 시설자료는 사용 가능 상태이며, UQ151 도로는 실제 공간파일이 없어 `DATA_NOT_AVAILABLE`이다. 시설자료는 `data/analysis/vworld_layer_inventory.json`에서 전체 파일 분류와 제외 사유도 확인한다.

# VWorld 공모전용 Python 공간분석 고도화 개발지침

## 1. 개발 목적

기존 `Uiseong-Young-Researchers` 분석과 Leaflet Web GIS를 유지하면서, VWorld 공모전 「공간정보 활용 모델」 제출에 필요한 인구감소지역 진단, 국가공간정보 결합, 전통 수리시설 활용유형 분석을 추가한다.

기존 코드는 삭제하거나 전면 재작성하지 않는다. 다음 기존 기능을 보존한다.

- 696개 원자료 검증 및 의성군 경계 내부 427개 시설 선별
- EPSG:5174 → EPSG:4326 좌표변환, 시설 GeoJSON, 읍·면 Spatial Join
- 시설 수·저수용량 통계, 최근접거리, Nearest Neighbor Ratio, DBSCAN
- 500m·1km Buffer, 농업지역 Intersection, Pearson/Spearman 상관분석
- Leaflet Web GIS와 JSON/GeoJSON 정적 데이터 전달

새 분석은 `analysis/`의 별도 모듈로 추가하고 기존 결과와 비교 가능하게 한다.

## 2. 핵심 원칙

### 원칙 1. 없는 데이터를 생성하지 않는다

실제 인구·도로·생활시설 공공데이터를 확보하지 못하면 임의 수치나 simulated data를 만들지 않는다. 결측 상태는 `DATA_NOT_AVAILABLE`로 기록한다.

### 원칙 2. VWorld 사용 여부를 증명한다

VWorld 자료/API를 실제 분석에 사용한 경우 다음을 `data/manifests/vworld_sources.csv`에 남긴다.

- 데이터명, 제공기관, VWorld 레이어/API명
- 다운로드·요청일, 원본 CRS, 사용 목적, 가공방법
- 라이선스와 이용조건

실제 VWorld 원자료가 없으면 VWorld를 사용했다고 표현하지 않는다.

### 원칙 3. 원본과 가공물을 분리한다

```text
data/raw/          원본·대용량 다운로드 자료
data/processed/    Clip·정제·분석용 자료
data/geojson/      Web GIS 전달자료
data/analysis/     분석 결과
data/manifests/    출처·획득·라이선스 기록
```

대용량 원본은 GitHub에 올리지 않고 출처와 획득방법만 manifest와 README에 기록한다.

## 3. 분석 CRS

- 웹 표시: `EPSG:4326`
- 거리·면적: 한국 중부지역에 적합한 미터 단위 투영좌표계
- 현재 자료와의 정합성을 위해 `EPSG:5174`를 우선 검토
- EPSG:4326 위경도에서 직접 거리·Buffer를 계산하지 않음
- 분석 후 Web GIS 전달자료만 EPSG:4326으로 변환

## 4. 분석 모듈 구조

```text
analysis/
├─ prepare_data.py
├─ advanced_analysis.py
├─ prepare_population.py
├─ prepare_vworld.py
├─ population_analysis.py
├─ accessibility_analysis.py
├─ pond_context_analysis.py
├─ classify_ponds.py
├─ build_competition_outputs.py
└─ acquire_worldpop.py       # 참고용 100m WorldPop 확보
```

## 5. Phase 1 — 인구 데이터 전처리

`prepare_population.py`는 읍·면별 총인구·연령별 인구·청년인구·65세 이상 인구·기준연도를 변환한다.

산출 필드:

```text
emd_code, emd_name, total_population, youth_population, youth_ratio,
elderly_population, elderly_ratio, population_change, year
```

청년 기준은 하나로 확정하여 README와 결과에 명시한다. 산출물은 다음과 같다.

```text
data/processed/population/uiseong_population.csv
data/geojson/uiseong_population.geojson
```

## 6. Phase 2 — VWorld 공간정보 전처리

행정경계, 도로를 최소 대상으로 하고 공공·문화·관광·생활시설을 추가 대상으로 한다. VWorld 실제 레이어를 확인한 뒤 데이터명을 확정한다.

```text
data/processed/roads/uiseong_roads.gpkg
data/processed/facilities/uiseong_facilities.gpkg
```

전국 원자료는 의성군 경계로 Clip하고, 원본 CRS와 가공 CRS를 기록한다.

## 7. Phase 3 — 인구감소지역 진단

`population_analysis.py`는 읍·면별 총인구, 인구증감률, 청년인구·비율, 고령인구·비율을 생성한다.

```text
data/analysis/population_summary.json
data/geojson/population_by_emd.geojson
```

필수 시각화는 총인구, 청년비율, 고령비율, 가능하면 최근 인구증감률이다.

## 8. Phase 4 — 도로 접근성

`accessibility_analysis.py`는 427개 시설별 최근접 도로거리와 접근성 구간을 계산한다.

```text
pond_id, nearest_road_m, accessibility_class
```

구간은 결과분포를 확인한 뒤 확정하며, 분석 전부터 정책판정을 임의로 부여하지 않는다.

```text
data/analysis/pond_accessibility.csv
data/analysis/pond_accessibility.json
```

## 9. Phase 5 — 시설 주변 생활권

500m·1km Buffer별 다음 지표를 계산한다.

```text
population, youth_population, elderly_population,
agricultural_area, facility_count, road_length, business_count
```

읍·면 총계만 있으면 정확한 Buffer 인구로 표현하지 않고 `pond_emd_population_context`로 분리한다. 격자 인구가 있을 때만 Buffer 내 인구를 직접 합산한다.

## 10. Phase 6 — 활용유형 분류

427개 시설을 다음 유형으로 분류한다.

```text
A_CULTURE_TOURISM
B_ECO_EDUCATION
C_COMMUNITY
D_PRESERVATION
E_MANAGEMENT_PRIORITY
```

변수는 도로 접근성, 주변 인구·청년·고령인구, 생활시설, 농업지역 비율, 규모·저수용량, 현장조사·관리상태다. 분류결과에는 반드시 `classification_reason`을 저장한다.

## 11. 분류방법 제한

처음부터 임의 가중치 점수를 만들지 않는다. 변수별 `min`, `max`, `mean`, `median`, `quartile`, `missing_count`를 확인한다. 가중치나 규칙은 [`methodology.md`](methodology.md)에 근거와 함께 기록한다. 근거가 약하면 설명 가능한 규칙 기반 분류를 우선한다.

## 12. 권장 분류방식

- 문화·관광형: 접근성 상위 AND 주변 생활·문화시설 존재
- 생태·교육형: 농업·자연환경 비율 상위 AND 개발밀도 낮음
- 공동체형: 주거·마을과 가까움 AND 주민·고령인구 수요 존재
- 보존·기록형: 접근성은 낮지만 보존·역사 속성 존재
- 관리우선형: 현장 관리상태가 낮거나 관리정보 보완 필요

## 13. 공모전 결과파일

```text
data/analysis/competition/
├─ population_summary.json
├─ accessibility_summary.json
├─ pond_context.json
├─ pond_classification.json
├─ pond_classification_summary.json
└─ competition_metrics.json
```

지도자료:

```text
data/geojson/population_by_emd.geojson
data/geojson/ponds_accessibility.geojson
data/geojson/ponds_context.geojson
data/geojson/ponds_classified.geojson
```

## 14. 그림 자동생성

`analysis/figures/`에 다음 10종을 Python으로 생성한다.

```text
01_population_trend.png
02_youth_elderly.png
03_population_map.png
04_youth_map.png
05_elderly_map.png
06_pond_distribution.png
07_pond_road_accessibility.png
08_pond_buffer_analysis.png
09_pond_classification.png
10_2025_2026_model_diagram.png
```

## 15. 보존해야 할 기존 정량결과

```text
원본 시설 696
분석 시설 427
총저수용량 39,578.75천톤
평균저수용량 56.89천톤
1km 평균 농업지역 약 40.63ha
1km 농업지역 × 저수용량 Spearman ρ=0.219
```

`ρ=0.219`는 강한 관계나 인과관계로 포장하지 않는다. 인구·접근성·생활환경을 결합해야 활용 가능성을 더 잘 설명할 수 있다는 수준으로 해석한다.

## 16. Web GIS 고도화

기존 Leaflet을 유지하고 총인구, 청년인구, 고령인구, 도로, 생활시설, 활용유형 레이어를 추가한다. Popup에는 시설 ID·읍면·저수량·도로거리·농업지역·인구정보·활용유형·분류근거·청년활동 추천을 표시한다.

## 17. VWorld 적용

기본지도 로고보다 실제 분석 데이터 사용흔적이 중요하다. README에 다음을 남긴다.

```text
데이터명:
레이어/API:
활용 목적:
가공:
분석:
산출물:
```

## 18. 데이터 검증

각 단계에서 CRS, geometry valid, duplicate, null, 의성군 경계 밖 자료, 시설 수 427 유지, Buffer 면적 단위, 거리 meter 단위, 공간조인 누락을 검증하고 `data/analysis/validation_report.json`에 저장한다.

## 19. 재현 가능한 실행

```bash
python analysis/run_competition_pipeline.py
```

실행순서는 기존 시설 준비, 인구 준비, VWorld 레이어 준비, 인구분석, 접근성, Buffer·Context, 분류, 결과생성, 검증이다. WorldPop 참고자료 다운로드는 별도 명령으로 실행한다.

```bash
python analysis/acquire_worldpop.py
```

## 20. README

공모전 섹션은 다음 흐름을 설명한다.

```text
Problem → 2025 Field Research → 427 Local Resources → Public Spatial Data
→ Python Spatial Analysis → Resource Classification → Youth Activity Model
→ 2026 Similar Real-world Activity → Transferable Model
```

기존 포트폴리오 설명은 유지하고 공모전 정책목적은 별도 섹션에서 설명한다.

## 21. 금지사항

- 가상 인구데이터 생성
- VWorld 미사용 상태에서 사용했다고 작성
- 2026년 사업의 2025년 연구 채택을 단정
- 약한 상관관계를 강한 인과관계로 표현
- 좌표계가 다른 자료로 거리 계산
- 출처 없는 SHP 사용
- 기준연도 혼합 후 설명 누락
- 개인정보 포함 또는 유료 데이터 사용
- 기존 427개 분석결과 삭제
- 기존 Web GIS를 새 프레임워크로 전면 재작성

## 22. 개발 완료 기준

- [ ] 인구데이터 출처 확정
- [ ] 읍·면별 총인구·청년·고령 지도 생성
- [ ] VWorld 실제 사용 데이터 1~2종 확보 및 manifest 작성
- [ ] 427개 시설 도로접근성 계산
- [ ] 시설 주변 공간조건 분석
- [ ] 427개 활용유형·분류근거 생성
- [ ] 활용유형 지도와 Web GIS 반영
- [ ] 그림용 PNG 자동생성
- [ ] validation 통과
- [ ] README 분석방법 업데이트
- [ ] 공모전 정량지표 JSON 생성

원문 지침을 저장소에서 재현 가능한 Markdown 문서로 정리한 파일이다. 실제 진행상태는 [`implementation-status.md`](implementation-status.md)에서 별도로 관리한다.

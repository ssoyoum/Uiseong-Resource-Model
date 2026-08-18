# 박소영 | 토목·GIS 데이터 기반 개발자 포트폴리오

## GIS 데이터 분석 웹 포트폴리오

### 1. Project Overview

토목·수자원 분야에서 다뤄온 공간데이터와 현장 데이터 경험을 Python, AI, Web GIS로 확장하는 박소영의 개발자 포트폴리오입니다.

의성의 전통 농업유산인 '못'을 매개로 지역의 공간데이터를 구축하고, GIS 분석을 수행한 연구를 **웹 기반 인터랙티브 포트폴리오**로 재구성했습니다.

[🌐 Live Demo](https://ssoyoum.github.io/Uiseong-Young-Researchers/)
[📁 GitHub Repository](https://github.com/ssoyoum/Uiseong-Young-Researchers)
---

## 2. About & Career

- 서울과학기술대학교 건설시스템공학과·환경공학과 복수전공
- 토목기사
- 온실가스종합정보센터: NGMS 시스템 사용자 상담 및 문의 대응
- 한국시설안전공단: FMS 점검·진단 보고서 56건 데이터 입력·검토
- 한국수자원조사기술원: 국가하천 유역조사, 유량·유사량 측정, 홍수피해조사
- 동부엔지니어링: 하천기본계획, 홍수위험지도, 해외 ODA, 조사자료 분석·보고서 작성

주요 도메인 기술은 BIM, ArcGIS, QGIS, CAD이며, 현재 HTML, CSS, JavaScript, Web GIS, Leaflet을 학습하고 있습니다.

## 3. Background

### 2.1 2025년 의성군 청년연구자 프로젝트

- **기간**: 2025.06 — 2025.09
- **역할**: 의성군 청년연구자 (GIS 데이터 분석)
- **대상**: 의성 전통수리시설 '못'
- **출력물**: GIS 데이터 구축, 공간 분석, 정책 제안

### 2.2 웹 포트폴리오 재구성

기존 QGIS 기반 분석을 웹 환경으로 재구성하면서, Python을 활용한 추가 공간 통계 분석을 수행했습니다.

---

## 4. Research Background

### 의성 전통수리시설 '못'

의성에는 오래전부터 농업용수를 확보하고 공동으로 이용하기 위한 전통 수리시설인 '못'이 존재해왔습니다.

- **국가중요농업유산 제10호** (2018년 지정)
- **ICID WHIS 등재** (2022년)
- **의성 농업의 핵심 인프라**: 지역 농업용수의 약 40% 이상 공급

이 프로젝트는 이러한 못들을 단순한 문화유산이 아니라 **공간 데이터로 분석할 수 있는 지역자산**으로 바라봤습니다.

---

## 5. My Role

### 데이터 구축

- 원본 696개 중 의성군 경계 안의 못 427개 사용
- 좌표 데이터 구축 및 변환 (EPSG:5174 → WGS84)
- GIS 공간정보 구축

### 공간 분석

- QGIS를 활용한 지역별 분포 분석
- 못 규모, 용량, 관리주체 통계
- Research Note: 시설 간 최근린거리 및 공간적 군집성 추가 검토
- 분석 A: 시설 규모·용량의 공간적 분포 분석
- 분석 B: pandas 집계 → GeoPandas spatial join → 차트·Leaflet 지도
- 분석 C: 못 × 농업지역 Buffer/Intersection 처리 파이프라인
- 못 주변 농업진흥지역 Buffer/Intersection 및 용량 상관분석

### 웹 포트폴리오 제작

- Python 데이터 전처리 및 좌표 변환
- Leaflet을 이용한 Web GIS 구현
- 포트폴리오 페이지 개발

---

## 6. Data

### 6.0 Public portfolio deployment

이 프로젝트는 GitHub Pages로 공개할 수 있는 정적 웹 포트폴리오입니다.

1. VS Code 소스 제어에서 `.github/workflows/pages.yml`을 포함해 커밋합니다.
2. `Sync Changes` 또는 `Push`로 `main` 브랜치를 GitHub에 올립니다.
3. GitHub 저장소의 `Settings` → `Pages`로 이동합니다.
4. `Build and deployment`의 `Source`를 `GitHub Actions`로 선택합니다.
5. `Actions` 탭에서 `Deploy portfolio to GitHub Pages`가 성공하면 아래 주소를 공유합니다.

```text
https://ssoyoum.github.io/Uiseong-Young-Researchers/
```

이후 `main`에 Push할 때마다 Workflow가 HTML, CSS, JavaScript, GeoJSON, 분석 JSON을 자동으로 다시 배포합니다.

### 6.1 Source Data

| 데이터 | 출처 | 건수 | 형식 |
|--------|------|------|------|
| 못 위치 정보 | 의성군 주소 기반 | 696개 | 좌표 (WGS84) |
| 건물 경계 | GIS 건물 경계 데이터 | - | Polygon |
| 농업유산 정보 | 농림축산식품부 | - | 메타정보 |

### 6.2 Processed Data

| 파일 | 형식 | 내용 |
|------|------|------|
| `ponds.geojson` | GeoJSON | 못 위치, 용량, 관리주체 |
| `uiseong_boundary.geojson` | GeoJSON | 의성군 행정경계 |
| `region_summary.json` | JSON | 지역별 시설 통계 |
| `distance_cluster_summary.json` | JSON | 공간 통계 분석 결과 |
| `advanced_analysis.json` | JSON | 분석 A·B·C 및 Research Note 웹 시각화 결과 |
| `uiseong_emd.geojson` | GeoJSON | 읍면별 시설 수·면적·시설 밀도 지도 레이어 |
| `agricultural_areas.geojson` | GeoJSON | 의성군 경계와 겹치는 농지·농업진흥지역 |

---

## 7. Original Research

### QGIS 분석 결과

**총 조사 시설**: 696개

**총 저수 용량**: 39,578.75 천톤

**평균 용량**: 56.89 천톤

---

## 8. Web Reconstruction

기존 QGIS 기반 분석을 웹으로 재구성하면서:

1. **데이터 변환**: CSV → GeoJSON
2. **좌표 검증**: 모든 좌표 WGS84로 정규화
3. **웹 지도 구현**: Leaflet 기반 인터랙티브 맵
4. **분석 재현**: Python으로 공간 통계 생성

---

## 9. Python Analysis

### 좌표 변환

```python
from pyproj import Transformer

transformer = Transformer.from_crs("EPSG:5174", "EPSG:4326", always_xy=True)
lng, lat = transformer.transform(x, y)
```

### 공간 통계 분석

```python
from scipy.spatial.distance import cdist
import numpy as np

coordinates = np.array([[lat, lng] for lat, lng in pond_locations])
distances = cdist(coordinates, coordinates)
nearest_distances = np.min(distances[distances > 0], axis=1)
```

---

## 9. Web GIS

### Leaflet 구현

```javascript
// 경계 GeoJSON을 읽은 뒤 실제 bounds로 의성군에 맞춘다.
const map = L.map('map');
const boundaryLayer = L.geoJSON(boundaryGeoJSON).addTo(map);
const bounds = boundaryLayer.getBounds();
map.fitBounds(bounds, { padding: [24, 24] });
```

### 주요 기능

- 의성군 중심 맵 표시
- 못 위치 마커 (크기 = 용량)
- 용량별 필터링
- 마커 클릭 시 상세정보 Popup
- 의성군 행정경계 표시
- 의성군 경계 밖 못 위치 제외

---

## 10. Tech Stack

### Backend & Data Processing
- Python 3.10 · pandas · GeoPandas · pyproj · scipy

### Frontend & Visualization
- HTML5 · CSS3 · JavaScript (ES6+) · Leaflet 1.9.4 · OpenStreetMap

### Spatial Analysis
- 좌표 변환 (EPSG:5174 → WGS84) · GeoJSON · 최근접 이웃 분석

### Development Tools
- Git · GitHub · VS Code · Python virtual environment

---

## 11. Project Structure

```
Uiseong-Young-Researchers/
├── README.md                      # 이 파일
├── index.html                     # 메인 페이지
├── styles.css                     # 스타일시트
├── app.js                         # 맵 및 데이터 로직
│
├── data/
│   ├── geojson/
│   │   ├── ponds.geojson         # 의성군 내부 못 위치 (427개)
│   │   └── uiseong_boundary.geojson # 의성군 경계
│   │   ├── uiseong_emd.geojson   # 읍면별 시설 집계 지도
│   │   └── agricultural_areas.geojson # 농지·농업진흥지역
│   └── analysis/
│       ├── region_summary.json
│       ├── distance_cluster_summary.json
│       └── advanced_analysis.json # 분석 A·B·C 결과
│
└── 의성/  # 원본 데이터
```

---

## 12. Key Features

- ✅ 의성군 중심 Web GIS (fitBounds)
- ✅ 원본 696개 중 의성군 내부 427개 못 데이터 시각화
- ✅ 용량별 필터링
- ✅ 마커 클릭 상세정보
- ✅ 지역별 통계 분석
- ✅ 분석 A: 시설 규모·용량의 공간적 분포 분석
- ✅ 분석 B: GeoPandas spatial join 기반 읍면별 비교
- ✅ 분석 C: 못 × 농업지역 공간분석 과정 시각화
- ✅ 관리주체별 시설 수 원그래프·토지면적당 시설 수 dot plot
- ✅ 못 주변 500m·1km 농업지역 면적 분석
- ✅ 농경지·농업진흥지역 Leaflet 레이어 ON/OFF와 Polygon Popup
- ✅ 용량과 주변 농업환경의 Pearson·Spearman 상관분석
- ✅ 로그축 Scatter plot과 점별 마우스 상세정보
- ✅ 스크롤 진입 애니메이션·페이지 진행률 UI
- ✅ Python 공간 통계 분석

---

## 13. Results

| 항목 | 결과 |
|------|------|
| 원본 조사 시설 | 696개 |
| 의성군 경계 내 지도·분석 시설 | 427개 |
| 총 저수 용량 | 39,578.75 천톤 |
| 평균 용량 | 56.89 천톤 |
| 평균 최근접 거리 | 683.8m |
| Research Note | 강한 군집 패턴은 확인되지 않음 |
| Research Note DBSCAN | 13개 후보군집, 통계적 유의성 낮음 |
| 전체 용량 가중 중심 | 36.340232N, 128.567685E |
| 1km 주변 농업지역 평균 | 약 40.63ha |
| 용량 × 1km 농업지역 Spearman | ρ=0.219 (약한 양의 관계) |

---

**마지막 업데이트**: 2026년 8월
**상태**: MVP 완성

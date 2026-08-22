# 의성 농업유산 Web GIS

> **GIS Research Data → Python Analysis → Interactive Web GIS**

2025년 의성 청년연구자로 수행했던 전통수리시설 **'못' 연구 데이터를 웹 서비스 형태로 재구성한 개인 프로젝트**입니다.

기존 GIS 분석 결과를 정적인 지도와 보고서에 머무르게 하지 않고,
Python으로 데이터를 전처리·분석한 뒤 **Leaflet 기반 Interactive Web GIS**로 구현했습니다.

**[🌐 Live Demo](https://ssoyoum.github.io/Uiseong-Young-Researchers/)**

---

## 1. Project Overview

의성의 전통수리시설인 '못'을 대상으로 구축했던 위치·규모·용량·관리주체 등의 GIS 데이터를 웹에서 직접 탐색할 수 있도록 재구성했습니다.

이 프로젝트의 핵심 목표는 다음과 같습니다.

> **기존 GIS 분석 데이터를 실제 사용자가 탐색할 수 있는 웹 결과물로 확장할 수 있을까?**

### Project Flow

```text
Research Data
      ↓
GIS Data Validation
      ↓
Python / GeoPandas
      ↓
Spatial Analysis
      ↓
GeoJSON
      ↓
Leaflet Web GIS
      ↓
GitHub Pages
```

---

## 2. What I Did

### Data Processing

기존 연구에서 구축한 데이터를 웹에서 활용할 수 있도록 정리했습니다.

* 위치 데이터 검토
* 결측값 및 오류 확인
* 의성군 행정경계 기준 데이터 선별
* 좌표계 변환
* CSV / GIS 데이터를 GeoJSON으로 변환
* 농업지역 공간데이터 전처리

분석 및 Web GIS에는 **의성군 행정경계 내부에서 확인된 427개 시설**을 활용했습니다.

---

### GIS / Spatial Analysis

QGIS와 Python을 이용해 기존 공간정보를 웹에서 활용할 수 있는 데이터로 다시 구성했습니다.

주요 분석:

* 행정구역별 시설 분포
* 시설 규모 및 용량 분포
* 관리주체별 시설 비교
* 시설 간 거리 및 공간 분포
* 못 주변 농업지역 분석
* 시설 용량과 주변 농업지역의 관계

분석 결과가 강하지 않은 경우 과도한 결론을 내리기보다 데이터 특성과 분석 과정을 함께 기록했습니다.

---

### Python Data Processing

Python은 Backend 서버가 아니라 **GIS 데이터를 전처리하고 분석하여 Web GIS에 전달하기 위한 데이터 처리 도구**로 사용했습니다.

```text
CSV / GIS Data
      ↓
Data Cleaning
      ↓
Coordinate Transformation
      ↓
Spatial Join / Intersection
      ↓
Statistical Analysis
      ↓
JSON / GeoJSON
      ↓
Web Visualization
```

주요 라이브러리:

`pandas` `GeoPandas` `pyproj` `scipy`

---

## 3. Web GIS

QGIS에서 확인하던 공간정보를 브라우저에서 직접 탐색할 수 있도록 Leaflet으로 구현했습니다.

### 주요 기능

* 의성군 중심 지도
* 전통수리시설 위치 표시
* 시설 용량을 반영한 Marker
* 시설별 상세정보 Popup
* 용량 기준 Filter
* 의성군 행정경계 표시
* 농업지역 Layer
* Polygon 정보 확인
* Layer ON / OFF

사용자는 정적인 지도 이미지를 보는 대신 지도에서 시설을 직접 클릭하고 공간 데이터를 탐색할 수 있습니다.

---

## 4. Data Pipeline

웹 지도에서 공간데이터를 사용하기 위해 기존 좌표 데이터를 웹 환경에 맞게 변환했습니다.

```text
Original GIS Data
      ↓
Validation
      ↓
EPSG:5174
      ↓
WGS84
      ↓
GeoJSON Feature
      ↓
Leaflet
```

이 과정에서:

* 좌표계 차이
* 행정경계 외 데이터
* 결측값
* 중복 데이터
* 극단값

등을 함께 검토했습니다.

---

## 5. Key Results

| 항목                     |           결과 |
| ---------------------- | -----------: |
| 원본 조사 시설               |         696개 |
| Web GIS 활용 시설          |         427개 |
| 총 저수 용량                | 39,578.75 천톤 |
| 평균 용량                  |     56.89 천톤 |
| 1km 주변 농업지역 평균         |   약 40.63 ha |
| 용량 × 1km 농업지역 Spearman |    ρ = 0.219 |

상관관계가 강하지 않은 분석 결과는 강한 결론으로 해석하지 않고, GIS 데이터를 공간분석으로 변환하고 검토하는 과정 자체에 초점을 맞췄습니다.

---

## 6. Tech Stack

### GIS / Spatial Data

`QGIS` `ArcGIS` `GeoJSON`

### Data Analysis

`Python` `pandas` `GeoPandas` `pyproj` `scipy` `Jupyter Notebook`

### Web

`HTML` `CSS` `JavaScript` `Leaflet`

### Development

`Git` `GitHub` `GitHub Pages`

---

## 7. Project Structure

```text
Uiseong-Young-Researchers/
├── index.html
├── styles.css
├── app.js
│
├── analysis/
│
├── data/
│   ├── geojson/
│   │   ├── ponds.geojson
│   │   ├── uiseong_boundary.geojson
│   │   ├── uiseong_emd.geojson
│   │   └── agricultural_areas.geojson
│   │
│   └── analysis/
│       ├── region_summary.json
│       ├── distance_cluster_summary.json
│       └── advanced_analysis.json
│
└── .github/
    └── workflows/
```

---

## 8. What I Learned

이 프로젝트에서는 새로운 도메인을 선택하기보다, **기존에 가지고 있던 GIS·공간데이터 경험을 개발 기술로 확장하는 과정**에 집중했습니다.

### Data

GIS 데이터를 브라우저가 사용할 수 있는 형태로 바꾸기 위해 데이터 정제, 좌표 변환과 GeoJSON 구조를 직접 다뤘습니다.

### Python

pandas와 GeoPandas를 이용해 실제 공간데이터를 전처리하고 분석 결과를 웹에서 사용할 수 있는 데이터로 변환했습니다.

### Web

HTML, CSS, JavaScript를 이용해 분석 결과를 실제 사용자 화면으로 구현했습니다.

### Web GIS

Leaflet을 이용해 정적인 GIS 결과를 사용자가 직접 탐색할 수 있는 Interactive Map으로 확장했습니다.

---

## 9. Links

* **Live Demo:** https://ssoyoum.github.io/Uiseong-Young-Researchers/
* **Repository:** https://github.com/ssoyoum/Uiseong-Young-Researchers

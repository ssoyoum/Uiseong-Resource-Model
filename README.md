# 박소영 | 토목·GIS 데이터 기반 개발자

토목·수자원 분야에서 GIS와 공간데이터를 다뤄온 경험을 바탕으로, 데이터를 분석하고 웹 서비스로 구현하는 개발자를 목표로 하고 있습니다.

이 프로젝트는 2025년 의성 청년연구자로 수행했던 전통수리시설 **‘못’ 연구**를 웹 서비스로 재구성한 포트폴리오입니다. 기존 GIS 데이터를 Python으로 전처리·분석하고, Leaflet 기반 Interactive Web GIS로 구현했습니다.

<p>
  <a href="https://ssoyoum.github.io/Uiseong-Young-Researchers/">🌐 Live Demo</a>
  ·
  <a href="https://github.com/ssoyoum/Uiseong-Young-Researchers">📁 GitHub Repository</a>
</p>

---

## 목차

- [About Me](#about-me)
- [Career](#career)
- [Project](#project)
- [Project Flow](#project-flow)
- [Web GIS](#web-gis)
- [Data Visualization](#data-visualization)
- [Research Background](#research-background)
- [What I Learned](#what-i-learned)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Key Results](#key-results)
- [Future Development](#future-development)
- [Project Status](#project-status)

## About Me

### 학력 및 자격

- 서울과학기술대학교 건설시스템공학과·환경공학과 복수전공
- 토목기사

수자원 분야에서 약 3년간 근무하며 하천기본계획, 홍수위험지도, 국가하천 유역조사, 현장 데이터 조사 및 GIS 분석 업무를 수행했습니다.

업무에서 GIS와 공간데이터를 다루면서, 데이터를 분석하는 것에 그치지 않고 실제 사용자가 활용할 수 있는 형태로 만들어보고 싶다는 관심이 생겼습니다.

이후 Python, Jupyter, RAG, LLM 등을 학습하고 현재는 HTML, CSS, JavaScript, Web GIS 등을 공부하며 기존의 GIS·데이터 경험을 웹 개발로 확장하고 있습니다.

장기적으로는 특정 도메인에만 머무르기보다 데이터를 직접 다루고 이를 웹 서비스로 구현할 수 있는 개발자로 성장하는 것을 목표로 하고 있습니다.

## Career

| 기간 | 기관 | 주요 경험 |
| --- | --- | --- |
| 2022.06 ~ 2025.07 | 동부엔지니어링 | 하천기본계획, 홍수위험지도, 해외 ODA 사업, 조사자료 분석 및 보고서 작성 |
| 2021.04 ~ 2021.12 | 한국수자원조사기술원 | 국가하천 유역조사, 유량·유사량 측정, 홍수피해조사 및 데이터 정리 |
| 2020.08 ~ 2020.10 | 한국시설안전공단 | FMS 점검·진단 보고서 56건의 외관조사·재료시험 결과 입력 및 검토 |
| 2018.01 ~ 2018.03 | 온실가스종합정보센터 | NGMS 시스템 사용자 문의 및 데이터 입력 기준 상담 |

### 주요 도구

`QGIS` `ArcGIS` `CAD` `BIM` `Python` `pandas` `GeoPandas`

## Project

### 의성 농업유산 Web GIS

**기존 연구 데이터를 웹과 데이터 분석으로 재구성하다**

**기간:** 2025.06 ~ 2025.09<br>
**배경:** 의성군의 지원을 받아 청년연구자로 참여한 전통수리시설 ‘못’ 연구

의성의 전통수리시설인 ‘못’을 대상으로 GIS 데이터를 구축하고 공간분석을 수행했습니다. 당시 연구에서 정리한 못의 위치, 규모, 용량, 관리주체 등의 자료를 바탕으로 QGIS 분석을 진행했습니다.

이번 프로젝트에서는 기존 연구 결과를 그대로 보여주는 데서 그치지 않고, 개발 학습 과정에서 직접 웹 서비스 형태로 다시 구현했습니다.

## Project Flow

```text
기존 연구
   ↓
GIS 데이터 구축
   ↓
QGIS 공간분석
   ↓
Python 데이터 전처리·분석
   ↓
GeoJSON 변환
   ↓
Leaflet Web GIS 구현
   ↓
GitHub Pages 배포
```

### My Role 01. Data

기존 연구에서 구축한 못 데이터를 웹에서 사용할 수 있도록 정리하고 변환했습니다.

- 못 위치 데이터 정리
- 좌표 데이터 검토 및 변환
- 의성군 행정경계를 기준으로 데이터 정리
- CSV 데이터를 GeoJSON 형태로 변환
- 농업지역 공간데이터 전처리
- 결측값 및 데이터 오류 검토

원본 데이터 중 의성군 경계 안에 포함되는 **427개의 못**을 Web GIS와 분석에 활용했습니다.

### My Role 02. GIS Analysis

기존 QGIS 분석을 바탕으로 웹에서 활용할 수 있는 데이터 형태로 다시 구성했습니다.

- 행정구역별 시설 분포
- 시설 규모 및 용량 분포
- 관리주체별 시설 비교
- 시설 간 거리 및 공간적 분포
- 못 주변 농업지역 분석
- 시설 용량과 주변 농업지역의 관계

분석 과정에서 좌표계 차이, 결측 데이터, 극단값 등 데이터 특성도 함께 검토했습니다.

### My Role 03. Python Data Analysis

Python을 이용해 기존 GIS 데이터를 웹에서 활용할 수 있는 형태로 전처리하고 추가적인 공간분석을 수행했습니다.

#### 주요 사용 기술

`Python` `pandas` `GeoPandas` `pyproj` `scipy` `Jupyter Notebook`

#### 데이터 처리 과정

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

Python은 별도의 백엔드 서버를 구축하기 위한 용도보다는, GIS 데이터를 전처리하고 분석한 결과를 웹에서 활용할 수 있도록 만드는 과정에 활용했습니다.

## Web GIS

### Leaflet Interactive Map

기존 QGIS에서 확인하던 공간정보를 웹 브라우저에서 직접 탐색할 수 있도록 구현했습니다.

### 주요 기능

- 🗺️ 의성군 중심 지도 표시
- 📍 못 위치 시각화
- 📊 시설 용량에 따른 마커 표현
- 💬 시설 상세정보 Popup
- 🔎 용량별 필터링
- 🧭 의성군 행정경계 표시
- 🌾 농업지역 레이어 표시
- 📋 농업지역 Polygon 정보 확인
- 👁️ 지도 레이어 ON / OFF

사용자는 정적인 지도 이미지를 보는 대신 지도를 확대·축소하고 시설을 클릭하면서 각 시설의 정보를 직접 확인할 수 있습니다.

## Data Visualization

분석 결과를 단순한 표로 나열하기보다 웹에서 직접 탐색할 수 있도록 시각화했습니다.

### 주요 시각화

- 📊 시설 규모 및 용량 분포
- 🏘️ 읍면별 시설 분포
- 👥 관리주체별 비교
- 🌾 시설과 농업지역의 공간적 관계
- 📈 시설 용량과 주변 농업지역의 관계

세부 데이터는 필요한 경우 필터와 마우스오버 정보로 확인할 수 있도록 구성했습니다. 통계적으로 의미가 크지 않은 결과는 과도하게 강조하지 않고 Research Note에서 간략하게 다뤘습니다.

## Research Background

### 의성 전통수리시설 ‘못’

의성의 ‘못’은 농업용수를 확보하고 공동으로 이용하기 위해 오랜 기간 지역에서 활용되어 온 전통수리시설입니다.

의성 전통수리 농업시스템은 다음과 같은 농업유산으로서의 가치를 인정받고 있습니다.

| 구분 | 내용 |
| --- | --- |
| 🏛️ 국가중요농업유산 | 제10호 · 2018년 지정 |
| 🌏 세계관개시설물유산 | ICID WHIS · 2022년 등재 |
| 🌍 세계중요농업유산 | UN FAO GIAHS 등재 절차 추진 |

이번 프로젝트에서는 이러한 농업유산을 단순한 문화유산 정보가 아니라, 공간 데이터로 접근하고 분석할 수 있는 지역 데이터로 바라보았습니다.

### Research Insight

이번 분석의 목적은 새로운 정책을 제안하거나 지역의 문제를 단정하는 것이 아니라, **GIS 데이터가 웹 서비스에서 어떻게 활용될 수 있는지**를 직접 구현해보는 것이었습니다.

#### 분석에서 확인한 내용

- 못의 공간적 분포와 행정구역별 차이
- 못 주변 농업지역과 시설 용량의 관계
- 시설 간 거리를 이용한 공간적 군집 여부
- 통계적으로 강하지 않은 공간적 군집성
- 시설 용량과 주변 농업지역 사이의 약한 관계

따라서 통계적으로 의미가 제한적인 결과를 과도하게 해석하기보다, 데이터의 특성과 분석 과정 자체를 함께 기록하는 데 초점을 맞췄습니다.

## What I Learned

이번 프로젝트를 통해 기존 GIS 분석 결과를 웹 환경으로 옮기는 과정을 처음부터 직접 구성해보았습니다.

### 🗂️ Data

GIS 데이터를 웹에서 사용할 수 있는 GeoJSON 형태로 변환하고 정리했습니다.

- CSV 데이터 정리
- 좌표계 변환
- 결측값 및 오류 검토
- 공간데이터 전처리

### 🐍 Python

`pandas`와 `GeoPandas`를 이용해 데이터를 전처리하고 공간분석 결과를 생성했습니다. 분석 결과는 JSON과 GeoJSON 형태로 저장하여 웹에서 활용했습니다.

### 🌐 Web

HTML, CSS, JavaScript를 이용해 분석 결과를 실제 웹 화면으로 구성했습니다.

### 🗺️ Web GIS

Leaflet을 이용해 정적인 GIS 결과를 사용자가 직접 탐색할 수 있는 Interactive Map으로 구현했습니다.

### 🔧 Development

Git과 GitHub를 이용해 프로젝트를 관리하고 GitHub Pages를 통해 실제 웹에 배포했습니다.

## Tech Stack

| 분야 | 기술 |
| --- | --- |
| 🗺️ GIS / Domain | QGIS, ArcGIS, CAD, BIM |
| 🐍 Data Analysis | Python, pandas, GeoPandas, pyproj, scipy, Jupyter Notebook |
| 🌐 Web | HTML5, CSS3, JavaScript, Leaflet |
| 🔧 Development | Git, GitHub, VS Code |
| 🤖 AI | RAG, LLM, ChromaDB |

AI 관련 기술은 별도의 프로젝트 경험을 바탕으로 학습하고 있으며, 현재는 웹 개발 역량을 확장하고 있습니다.

## Project Structure

```text
Uiseong-Young-Researchers/
├── index.html
├── styles.css
├── app.js
├── README.md
├── data/
│   ├── geojson/
│   │   ├── ponds.geojson
│   │   ├── uiseong_boundary.geojson
│   │   ├── uiseong_emd.geojson
│   │   └── agricultural_areas.geojson
│   └── analysis/
│       ├── region_summary.json
│       ├── distance_cluster_summary.json
│       └── advanced_analysis.json
└── 의성/
    └── 원본 데이터
```

## Key Results

| 항목 | 결과 |
| --- | ---: |
| 원본 조사 시설 | 696개 |
| 의성군 경계 내 활용 시설 | 427개 |
| 총 저수 용량 | 39,578.75 천톤 |
| 평균 용량 | 56.89 천톤 |
| 1km 주변 농업지역 평균 | 약 40.63 ha |
| 용량 × 1km 농업지역 Spearman | ρ = 0.219 |

세부 분석 결과와 시각화는 [Live Demo](https://ssoyoum.github.io/Uiseong-Young-Researchers/)에서 확인할 수 있습니다.

## Links

- [🌐 Live Demo](https://ssoyoum.github.io/Uiseong-Young-Researchers/)
- [📁 GitHub Repository](https://github.com/ssoyoum/Uiseong-Young-Researchers)

## Future Development

현재 프로젝트는 정적 웹 기반 MVP로 구현되어 있습니다.

향후에는 다음과 같은 방향으로 확장할 수 있습니다.

- ⚛️ React 기반 컴포넌트 구조로 전환
- 🔌 API를 통한 데이터 처리 및 조회
- 🗄️ 데이터베이스 연동
- 🔎 사용자 검색 및 고급 필터 기능
- 🗺️ 공간데이터 기반 추가 분석
- 📱 모바일 환경 최적화

현재는 HTML, CSS, JavaScript를 중심으로 웹 개발의 기본기를 학습하고 있으며, 향후 React와 백엔드 기술까지 학습 범위를 확장할 예정입니다.

## 실행 방법

정적 파일 기반 프로젝트이므로 간단한 로컬 서버로 실행할 수 있습니다.

```bash
python -m http.server 5500
```

브라우저에서 아래 주소로 접속합니다.

```text
http://localhost:5500
```

## Project Status

| 항목 | 상태 |
| --- | --- |
| GIS 데이터 구축 | ✅ 완료 |
| Python 데이터 분석 | ✅ 완료 |
| GeoJSON 변환 | ✅ 완료 |
| Leaflet Web GIS | ✅ 완료 |
| 데이터 시각화 | ✅ 완료 |
| GitHub Pages 배포 | ✅ 완료 |
| MVP | ✅ 완료 |
| React 전환 | 🔄 향후 계획 |
| Backend / DB 연동 | 🔄 향후 계획 |

---

**Last Updated:** 2026.08<br>
**Status:** MVP Complete

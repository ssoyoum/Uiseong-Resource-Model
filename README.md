# SGIS 지역통계를 활용한 인구감소지역 유휴자원 정책검토 모델

**의성군 전통수리시설 ‘못’ 427개를 첫 사례로 적용한 공개 Web GIS와 분석 파이프라인**입니다. 지역자원을 곧바로 활용 대상으로 정하기보다, SGIS 생활권 인구와 인구구조·접근성·주변시설·데이터 품질을 함께 살펴 **활용 검토, 보존·관리, 현장 확인, 데이터 보완**의 근거를 구분합니다.

[공개 화면](https://ssoyoum.github.io/Uiseong-Resource-Model/) · [SGIS 생활권 분석](https://ssoyoum.github.io/Uiseong-Resource-Model/#analysis-d) · [정책 검토 결과](https://ssoyoum.github.io/Uiseong-Resource-Model/#analysis-e) · [시설 지도](https://ssoyoum.github.io/Uiseong-Resource-Model/#webgis)

## 모델과 의성 사례

| 단계 | 공통 검토 절차 | 의성 사례의 구현 |
| --- | --- | --- |
| 자원 발굴·정리 | 시설 ID, 위치, 좌표 품질 확인 | 군 경계 내 못 427개를 같은 ID로 연결; 좌표 조건 통과 380개 |
| 생활권·지역 맥락 | SGIS 도달인구에 지역 인구구조와 공간환경 결합 | 2024년 SGIS 5분·10분 주행생활권 인구, 행정안전부 읍·면 인구, VWorld 도로·주변시설 |
| 정책 검토 | 근거가 있는 후보와 현장·데이터 보완 대상을 분리 | 6개 상호배타적 정책 검토 맥락 및 시설별 근거표 |

2025년 의성 청년연구자 활동에서 ‘못’ 기반 정책을 제안한 것이 출발점입니다. 이번 프로젝트는 저장된 SGIS 응답을 결합해 **다른 인구감소지역의 유휴·저활용 자원을 검토할 수 있는 절차**로 정리했습니다. 의성 외 지역에서의 적용은 아직 검증하지 않았습니다. [2026년 의성의 대학생 참여 활동](https://www.mafra.go.kr/bbs/home/792/578423/artclView.do)은 유사한 방향의 **별도 사업**이며, 이 모델이 해당 사업을 발생시켰거나 정책 성과를 실증했다는 뜻은 아닙니다. [연구·출처·관련 보도 정리](docs/submission/sgis-achievements-and-sources.md)

## 확인된 결과

| 항목 | 결과 | 해석 |
| --- | ---: | --- |
| 의성군 경계 내 못 | 427개 | 고유 시설 ID 기준 |
| 좌표 품질 조건 통과 | 380개 | 나머지 47개는 좌표·현장 확인 필요 |
| SGIS 5분 인구 확보 | 175개 | 조건 통과 시설 기준 |
| SGIS 10분 인구 확보 | 190개 | 조건 통과 시설 기준; 190개는 10분 인구 미확보 |
| 5분·10분 모두 확보 | 175개 | 두 생활권 인구 비교 표본 |

6개 정책 검토 맥락의 시설 수는 **접근·도달 20개, 청년참여 43개, 공동체 지원 53개, 현장 확인 필요 47개, SGIS 10분 인구 미확보 190개, 맥락 참고 74개**입니다. 합계는 427개이며, 앞의 세 맥락에 속한 116개에 대해 현장검토 양식을 만들었습니다. 이는 정책 채택이나 현장검증 완료를 뜻하지 않습니다. [시설별 근거표](data/analysis/sgis_policy_evidence.csv) · [판정 방법](docs/sgis-policy-comparison.md)

별도 규칙기반 활용유형은 보존·기록형 329개, 문화·관광형 55개, 생태·교육형 43개입니다. 이 분류에는 SGIS 인구가 입력되지 않았으며, 현장 보존가치나 생태가치가 확정된 결과가 아닙니다. [활용유형 표](data/analysis/pond_classification.csv)

## 공개 화면

- **시설 지도:** 427개 못의 위치·속성, 읍·면과 활용유형 필터, 시설별 데이터 상태.
- **생활권 분석 D:** SGIS 5분·10분 인구 산점도와 시설별 비교. 그래프에서 점을 선택해 지도 위치를 확인할 수 있습니다.
- **정책 검토 E:** 6개 검토 맥락의 분포와 각 시설의 판정 근거.
- **도로·인구 F:** VWorld 도로 객체까지의 최근접 **직선거리**와 행정안전부 읍·면 인구 변화.

정적 페이지는 사전에 수집·검증한 분석 결과를 보여줍니다. 브라우저에서 SGIS OpenAPI를 실시간으로 호출하지 않습니다. 지도 인터페이스는 저장소에 포함한 Leaflet 1.9.4를 사용합니다([라이선스](vendor/leaflet/LICENSE)).

## 원자료와 해석 범위

| 자료 | 사용 범위 | 기록 |
| --- | --- | --- |
| 작성자의 2025년 의성 청년연구 못 목록 | 시설 위치·속성의 출발점 | [정제 목록](data/processed/ponds.csv), [선행자료·출처](docs/submission/sgis-source-and-press-evidence.md) |
| SGIS 생활권역 통계지도·개발지원센터 OpenAPI | 2024년 5분·10분 주행생활권 인구 | [출처 manifest](data/manifests/sgis_sources.csv), [저장 응답](data/processed/population/sgis_drive_population.csv) |
| VWorld UQ151·UQ164·UO601 | 도로 객체와 주변 시설 맥락 | [출처 manifest](data/manifests/vworld_sources.csv), [접근성 표](data/analysis/pond_accessibility.csv) |
| 행정안전부 주민등록 인구 | 2024·2025년 12월, 18개 읍·면 청년·고령 인구 | [출처 manifest](data/manifests/population_sources.csv), [요약](data/analysis/population_summary.json) |

SGIS 생활권 인구는 실제 방문객 수가 아닙니다. 응답이 없는 시설은 **0명으로 대체하지 않았습니다.** 시설별 생활권은 겹칠 수 있으므로 인구값을 합산하지 않습니다. VWorld 도로거리는 네트워크 이동거리나 주행시간이 아닙니다. 읍·면 인구는 지역 배경지표이며 시설 주변 인구가 아닙니다. 국내 공식 인구격자 기반 500m·1km 인구는 `DATA_NOT_AVAILABLE`입니다. [SGIS 분석 방법과 결측 처리](docs/sgis-catchment-analysis.md)

## 실행과 검증

Python 3에서 공개용 정적 파일을 만들고 로컬 서버로 확인할 수 있습니다.

```powershell
python analysis/build_public_site.py --output _site
python -m http.server 8000 --bind 127.0.0.1 --directory _site
```

전체 공간분석을 재생성하려면 저장소의 원자료와 GIS 라이브러리가 필요합니다. 공개 저장소에 없는 원자료를 임의로 만들지 않습니다.

```powershell
python analysis/run_competition_pipeline.py
```

공개 빌더는 시설 ID, SGIS 응답 범위, 정책 그룹, 검증 보고서를 대조한 뒤 필요한 파일만 복사합니다. GitHub Pages 배포는 [workflow](.github/workflows/pages.yml)를 사용합니다. [검증 보고서](data/analysis/validation_report.json) · [제출 주장 점검](data/analysis/submission_claims_report.json)

다음 단계는 좌표·시설 상태 현장 확인, 미확보 SGIS 값 재수집, 다른 인구감소지역의 소규모 사례로 절차를 시험하는 것입니다.

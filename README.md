# SGIS 지역통계를 활용한 인구감소지역 유휴자원 정책검토 모델

SGIS **생활권역 통계지도·개발지원센터 OpenAPI**의 주행생활권 인구를 지역자원에 연결해 정책 검토 근거를 만드는 프로젝트입니다. 의성군 전통수리시설 **‘못’ 427개**를 첫 사례로 적용했습니다.

[공개 Web GIS](https://ssoyoum.github.io/Uiseong-Resource-Model/) · [SGIS 인구 비교](https://ssoyoum.github.io/Uiseong-Resource-Model/#analysis-d) · [정책 검토 결과](https://ssoyoum.github.io/Uiseong-Resource-Model/#analysis-e)

## 모델의 흐름

**자원 목록·좌표 검증 → SGIS 5분·10분 생활권 인구 확인 → 지역 인구·도로·주변시설 결합 → 정책 검토 맥락 구분 → 현장 확인**

2025년 의성 청년연구자 활동에서 정리한 못 자료와 정책 제안을 출발점으로 삼았습니다. 이번 분석에서는 SGIS 지역통계를 더해 시설별 근거와 데이터 보완 대상을 구분했습니다. [분석 방법](docs/sgis-catchment-analysis.md) · [정책 검토 기준](docs/sgis-policy-comparison.md)

## 의성 사례의 검증 결과

- 의성군 경계 내 못 **427개**를 고유 시설 ID로 연결하고, **380개**가 SGIS 분석용 좌표 조건을 통과했습니다.
- SGIS 인구 기준연도 **2024년**. 5분 인구 **175개**, 10분 인구 **190개**, 두 시간대 모두 **175개** 시설에서 확보했습니다.
- 전체 427개를 **6개 상호배타적 정책 검토 맥락**으로 정리하고, 접근·도달·청년참여·공동체 지원 맥락 **116개**의 현장검토 양식을 만들었습니다. [시설별 근거표](data/analysis/sgis_policy_evidence.csv)

SGIS 미응답은 인구 **0명**으로 바꾸지 않았습니다. 생활권 인구는 실제 방문객 수가 아니며, 정책 맥락은 정책 채택이나 효과 검증 결과가 아닙니다. 타 지역 적용도 후속 검증 대상입니다.

## 자료와 실행

SGIS 생활권 응답은 [SGIS 출처 기록](data/manifests/sgis_sources.csv), 읍·면 인구는 [행정안전부 출처 기록](data/manifests/population_sources.csv), 도로·주변시설은 [VWorld 출처 기록](data/manifests/vworld_sources.csv)에서 확인할 수 있습니다. VWorld 도로거리는 도로 객체까지의 **직선거리**입니다.

```powershell
python analysis/run_competition_pipeline.py
python analysis/build_public_site.py --output _site
python -m http.server 8000 --bind 127.0.0.1 --directory _site
```

전체 분석 재실행에는 별도로 보관한 원자료와 GIS 라이브러리가 필요합니다. [검증 보고서](data/analysis/validation_report.json) · [공개 분석 화면](https://ssoyoum.github.io/Uiseong-Resource-Model/)

# CODEX 개발지침 — VWorld 공모전 제출본 고도화

대상 저장소: `Uiseong-Resource-Model`  
목적: 제8회 공간정보 활용·아이디어 경진대회 「공간정보 활용 모델」 제출을 위한 분석·산출물 고도화  
원칙: 제출문서에 적을 수 있는 것은 실제 구현·재현·검증된 결과뿐이다.

## 1. 절대 규칙

- 결과를 만들어내기 위해 수치를 임의 생성하지 않는다.
- 미확보 데이터는 `DATA_NOT_AVAILABLE` 또는 명확한 상태값으로 유지한다.
- WorldPop은 국내 공식 인구격자의 대체자료로 표현하지 않는다.
- 군 단위 교통문화지수를 시설별 접근성 점수로 복제하지 않는다.
- VWorld UQ151 도로를 확보하지 않은 상태에서 도로거리 결과를 실제값처럼 생성하지 않는다.
- Random Forest, F1, 정확도, 우선순위점수 등은 실제 학습·검증 코드와 결과가 존재할 때만 문서에 반영한다.
- 기존 사용자 변경 `index.html`은 별도 승인 없이 수정·커밋하지 않는다.
- 루트 `vworld/` 원자료는 이동·삭제·Git 추적하지 않는다.
- `.gitignore` 대상 원자료를 `git add -f`로 강제추적하지 않는다.
- 경로·파일명·기준연도·출처는 manifest와 문서가 반드시 일치해야 한다.

## 2. 2026-08-31 기준 확인된 현재 상태

### 완료·검증됨

- 대상 저장소: `Uiseong-Resource-Model`
- `python analysis/run_competition_pipeline.py`: `pipeline: PASS`
- validation: `12 PASS / 0 FAIL`
- Python 문법검사: PASS
- Markdown 내부링크 오류: 0
- 행정안전부 주민등록 연령별 인구 2024·2025 처리
- 의성군 18개 읍·면 처리
- 청년 기준 만 19~39세
- 고령 기준 만 65세 이상
- VWorld UQ164·UO601 시설 처리
- 의성군 VWorld 시설 68개
- VWorld UQ151 도로 원자료 확보·의성군 Clip·427개 최근접거리 처리
- UQ151 500m·1km Buffer 도로 geometry 길이 산출
- 시설 500m·1km 주변조건 산출
- WorldPop 한국 100m 참고자료 확보 및 manifest 기록
- 교통문화지수 의성군 배경지표 산출
- 접근성·활용유형 관련 분석 산출물 생성
- CSV / JSON / GeoJSON / GPKG / PNG 산출물 생성
- 루트 `vworld/`를 VWorld 원자료 위치로 사용

### 아직 완료성과로 주장하면 안 되는 항목

- 국내 공식 인구격자 기반 500m·1km 인구
- Random Forest GeoAI 분류모델
- 정확도 87.2%, F1 0.85
- 정책우선순위 0~100 점수
- 상위 50개 정책후보지의 실제 산출
- Flask 기반 VWorld 실시간 API 프록시
- 실시간 VWorld API Web GIS 연동
- `classification_model.pkl`
- 타 지역 즉시 적용 가능한 완성형 diffusion kit
- 30쪽 사용자 매뉴얼
- 3분 데모영상
- 현장조사 시간·비용 88.3% 절감의 실증

## 3. 공모전 평가기준에 맞춘 개발 우선순위

2026년 1차 서면심사 기준:

- 독창성 15
- 혁신성 15
- 정확성 15
- 데이터 다양성 15
- 데이터 수급성 20
- 완성도 20

개발은 기능 개수보다 위 평가기준을 증명할 수 있는 산출물에 우선한다.

## 4. P0 — 제출 정확성·재현성 유지

### 4.1 파이프라인 회귀검증

모든 변경 후 다음을 실행한다.

```powershell
python analysis/run_competition_pipeline.py
```

필수 검증:

- validation FAIL = 0
- 기존 핵심 결과파일 누락 없음
- Python syntax PASS
- Markdown path/link 오류 없음

### 4.2 제출근거 manifest 정리

각 데이터 manifest에는 다음 필드를 갖춘다.

```text
dataset_name
provider
layer_id
reference_year
download_url
accessed_at
crs
license_url
local_source_path
processed_output
usage_note
redistribution_status
```

문서의 데이터 표와 manifest를 자동 또는 반자동으로 대조할 수 있게 한다.

## 5. P1 — VWorld 도로 UQ151

현재 `vworld/C_UQ151.zip` 원자료가 확보되어 있으므로 다음을 기준으로 유지·검증한다.

해야 할 일:

- UQ151 SHP 구성요소 확인: SHP, SHX, DBF, PRJ
- CRS 확인
- 의성군 범위 Clip
- geometry valid 검사
- 시설 427개에 대해 최근접 도로거리 계산
- 단위 meter 검증
- `distance_to_road_m`, `road_access_status`, `road_source_year` 필드 생성
- validation 항목 추가
- GeoJSON·분석 JSON·figure 갱신

금지:

- 도로가 없을 때 OSM 값을 VWorld UQ151 값으로 표시하지 않는다.
- 유클리드거리와 네트워크 이동거리를 혼용하지 않는다.
- 어떤 거리인지 문서와 필드명에서 명시한다.

## 6. P1 — 국내 공식 인구격자

공식 인구격자가 확보될 때만 다음 기능을 추가한다. 현재 읍·면 총계와 SGIS 화면 결과만으로는 이 항목을 완료 처리하지 않는다.

- 500m Buffer 인구
- 1km Buffer 인구
- 청년인구
- 고령인구

권장 필드:

```text
official_population_500m
official_population_1km
official_youth_population_1km
official_elderly_population_1km
population_grid_reference_year
```

WorldPop을 연결할 경우 반드시 별도 이름으로 관리한다.

```text
worldpop_population_500m
worldpop_population_1km
```

## 7. P2 — 분류 고도화

현재 분석·규칙기반 활용유형을 먼저 검증한다.

### 7.1 표본검토

- 각 유형별 표본 시설 추출
- `classification_reason` 확인
- 원자료 속성·지도와 대조
- fallback 발생원인 집계
- `D_PRESERVATION` 또는 기타 fallback 비율 확인

### 7.2 머신러닝은 별도 실험으로 진행

Random Forest를 구현하려면 먼저 정답 라벨의 출처를 정의해야 한다.

필수 조건:

- 누가 427개의 A~E 정답을 부여했는가
- 라벨 기준이 무엇인가
- 학습·검증 데이터 누수가 없는가
- 결측값을 어떻게 처리했는가
- class imbalance가 있는가

실험 산출물:

- confusion matrix
- per-class precision/recall/F1
- macro/weighted F1
- feature importance
- random seed
- split 방법
- model version

이 조건을 만족하기 전에는 제출문서에 “GeoAI 자동분류 모델 구현 완료”라고 쓰지 않는다.

## 8. P2 — 정책 우선순위 점수

가중치 기반 0~100 점수는 정책 가정이므로 근거 없이 고정하지 않는다.

구현 시:

- 각 지표의 방향성 정의
- 결측 처리 정의
- Min-Max 등의 정규화 방식 기록
- 가중치 근거 기록
- 민감도 분석 수행
- 상위 후보가 가중치 변화에 얼마나 안정적인지 확인

권장 결과:

- 기본 시나리오
- 접근성 강조 시나리오
- 보전 강조 시나리오
- 청년활동 강조 시나리오

`top50`은 행정적으로 정해진 기준이 아니라면 “정책 우선후보 예시”로 표현한다.

## 9. P3 — Web GIS 고도화

현재 정적 Web GIS를 우선 안정화한다.

제출 전 우선 기능:

- 427개 시설 조회
- 활용유형 필터
- 읍·면 필터
- 시설 상세정보
- VWorld 주변시설 수
- 데이터 상태 표시
- 출처·기준연도 표시
- `DATA_NOT_AVAILABLE` 시각적 표시

실시간 API는 후순위다. Flask/VWorld API 프록시를 구현하려면 API 이용약관, 서버측 API key 보관, timeout/error handling, rate limit, CORS, cache, 요청 실패 시 fallback을 검토한다.

실제 운영 확인 전에는 제출문서에 “실시간 연동 구현 완료”로 쓰지 않는다.

## 10. P2 — 그림 제작

제출본용 핵심 그림을 자동 생성할 수 있게 한다. 권장 최대 14개:

- 인구변화 그래프
- 청년·고령 변화
- 전체 모델 흐름도
- 696→427 정제 흐름
- 427개 분포지도
- 인구 공간진단 지도
- VWorld 시설 결합 지도
- 500m·1km 분석 지도
- 농업환경 분석
- 활용유형 분류지도
- 파이프라인 구조
- validation 요약
- Web GIS 화면
- 확산모델 개념도

규칙:

- 실제 결과와 개념도를 구분한다.
- 결과 그림은 입력파일·생성스크립트를 기록한다.
- 지도 CRS와 범례를 검토한다.
- 캡션용 출처 문자열을 metadata로 남긴다.

## 11. P3 — 확산키트

실제 다른 지역 적용을 검증하기 전에는 “코드 한 줄 수정 없이 적용”을 주장하지 않는다.

최소 확산키트:

- README
- input schema
- 예시 데이터
- requirements
- pipeline 실행법
- 데이터 필수/선택항목
- 오류메시지
- 출력 schema

가능하면 의성 외 1개 소규모 샘플로 재현 테스트 후 확산가능성을 기술한다.

## 12. 제출문서 자동 점검

가능하면 `analysis/validate_submission_claims.py` 형태의 점검 스크립트를 만든다.

검사 예:

- 문서의 숫자 427 / 68 / 기준연도 일치
- 존재하지 않는 산출파일명이 문서에 적혀 있지 않은지
- UQ151 미확보 상태와 도로결과 주장 충돌 여부
- WorldPop과 공식인구 혼용 여부
- 문서의 GitHub/웹 URL 유효 형식
- `DATA_NOT_AVAILABLE` 상태 체크
- validation PASS 여부

## 13. 커밋 규칙

기능 단위 커밋을 유지한다.

예:

```text
feat(roads): add UQ151 road accessibility
feat(population): add official grid buffer population
feat(classification): validate resource type rules
feat(model): add experimental RF classifier
feat(priority): add scenario-based policy scoring
feat(web): expose competition analysis layers
docs(submission): align claims with verified outputs
```

기존 사용자 변경을 섞지 않는다.

## 14. Codex 작업 완료 보고 형식

각 작업 종료 시 다음만 보고한다.

- 구현한 기능
- 사용한 실제 원자료
- 생성·수정 파일
- validation 결과
- 새로 제출문서에 쓸 수 있게 된 검증된 사실
- 아직 제출문서에 쓰면 안 되는 미구현 항목
- 다음 우선 TODO

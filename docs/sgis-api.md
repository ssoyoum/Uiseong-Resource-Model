# SGIS API 연동

## 인증값 보관

실제 인증값은 저장소 루트의 `.env`에만 보관한다.

```env
SGIS_CONSUMER_KEY=발급받은 consumer_key
SGIS_CONSUMER_SECRET=발급받은 consumer_secret
```

`.env`와 `.env.*`는 Git에서 제외되며, 공유 가능한 형식만 `.env.example`에 남긴다. 인증 토큰과 원격 응답 원문은 파일이나 로그에 저장하지 않는다.

## 검증 명령

```bash
python analysis/sgis_api.py auth-check
python analysis/sgis_api.py population-check --year 2020 --adm-cd 47730
```

검증 결과 요약은 `data/analysis/sgis_api_status.json`에 기록된다. 이 파일에는 인증 토큰과 인증값을 포함하지 않는다.

## 생활권역 5분·10분 인구

SGIS 생활권역 화면의 주행시간 인구는 공식 `serviceAreaGeometry.json`과 `serviceAreaStatistics.json` 호출 흐름으로 2024년 5분·10분 값을 추출했다. 거주인구·격자 인구와 다른 도달 규모 지표이므로 `sgis_drive_population_5min`, `sgis_drive_population_10min`으로 별도 저장한다.

따라서 일반 인구 API 응답을 500m·1km Buffer 인구로 대체하거나, 생활권역 값을 공식 격자 Buffer 인구로 명명하지 않는다.

## 현재 확인 결과

- 인증 endpoint: 정상 인증 및 AccessToken 발급 확인
- 공식 인구 API 샘플 요청: 서울 시도 코드 `11`은 응답 확인
- 의성군 코드 `47730`: `검색결과가 존재하지 않습니다` 응답. 인증 실패가 아니므로 의성군 분석값으로 사용하지 않음
- 생활권역 5분·10분 값: 427개 못 × 2개 시간대 요청, `AVAILABLE` 455건, `DATA_NOT_AVAILABLE` 399건
- `DATA_NOT_AVAILABLE` 399건 중 384건은 SGIS 경로망이 좌표를 위치로 인식하지 못한 `unlocated` 응답이고, 15건은 생활권역은 반환됐으나 인구 필드가 없는 응답
- 미응답 건을 0명으로 바꾸거나 읍·면 총계로 임의 배분하지 않음

## 생활권역 추출 구현

화면에서 확인한 공식 서비스 호출 흐름을 사용한다.

1. `serviceAreaGeometry.json`에 시설 중심점(EPSG:5179), `LEAD_TIME`, 5분·10분 break를 요청한다.
2. 반환된 주행권역 polygon을 WKT로 변환한다.
3. `serviceAreaStatistics.json`에 polygon WKT와 기준연도를 POST한다.
4. 화면과 같은 `popsTotOgl` 값을 `sgis_population`으로 저장하고, API 총계 필드 `tot_ppltn_cnt`는 비교용으로 별도 보관한다.

전체 실행:

```bash
python analysis/acquire_sgis_catchment.py --year 2024 --minutes 5 10 --delay 0.2
```

결과는 `data/processed/population/sgis_drive_population.csv`에 854개 조합으로 저장되며, `pond_context_analysis.py`가 이를 읽어 시설별 `sgis_drive_population_5min`, `sgis_drive_population_10min`으로 연결한다. SGIS의 비밀보호 처리와 주행권역 미생성 건은 각각 `DATA_NOT_AVAILABLE` 상태로 보존한다.

## 지역통계 지표 선택 결과

공식 문서에 정의된 인구·연령·가구·주택·사업체 endpoint도 `analysis/check_sgis_indicators.py`로 점검했다. 의성군 코드 `47730`, 2020·2024년 기준으로 인구·가구·주택은 검색결과 없음, 사업체는 성공 응답이나 0건, 연령별 endpoint는 현재 요청 파라미터 기준 오류를 반환했다. 점검 결과는 `data/analysis/sgis_indicator_availability.json`에 저장한다.

따라서 이번 제출본의 SGIS 핵심 지표는 실제 값이 확보된 생활권역 5분·10분 인구로 선정한다. 행정 읍·면별 총인구·청년·고령 인구는 현재 확보된 행정안전부 주민등록 자료를 보조 지표로 유지하며, SGIS 지역통계 API가 `AVAILABLE`로 확인되기 전에는 SGIS 값으로 표기하지 않는다.

공식 참고문서: [SGIS 센서스 통계 API](https://sgis.mods.go.kr/developer/html/newOpenApi/api/dataApi/census.html), [SGIS 인증·사용방법](https://sgis.mods.go.kr/developer/html/newOpenApi/api/dataApi/authAndUseApi.html)

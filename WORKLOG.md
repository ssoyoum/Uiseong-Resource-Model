# WORKLOG

## 2026-09-09

- 사용자 제공 SGIS 심사기준(충실성 30·효과성 30·확산가능성 30·창의성 10)을 기준으로 로컬 최종 원고 `docs/submission/sgis-uiseong-final-draft.md` 수정. SGIS 활용 전후 비교, 연구·정책검토 준비 성과, 지역별 재사용·변경사항을 보강하고 상세 분류·검증은 별첨으로 분리.
- 저장된 SGIS 응답과 기존 원자료로 재분석: 전체 427개, 좌표 조건 통과 380개, 양쪽 인구 비교 175개, 현장검토 양식 116개를 재확인. 신규 API 수집·좌표 추정·현장검토 결과 입력은 수행하지 않음.
- `validate_submission_claims.py`에 실제 최종 초안과 `--require-submission` 추가. `validate_sgis_submission.py`에서 표·주요 수치, SGIS 원응답 값, 그림의 시설 ID·입출력 해시, 로컬 링크·URL 형식을 검사. 제출근거 검증 65 PASS / 0 WARN / 0 FAIL, 회귀 테스트 5개 통과. 자동검증은 모든 자유서술·정책효과·외부 URL 응답·DOCX 페이지 수 검증을 의미하지 않음.
- 제출 그림 3개 재생성·육안 확인. 산점도는 좌표 조건을 통과하고 5분·10분 인구가 모두 확보된 175개 ID만 사용. SGIS 읍면 그래프의 한글 폰트 설정 및 정책 근거 문서 재생성 시 비교문서 링크 보존을 보완.
- 전체 파이프라인 PASS; 공간 검증 16 PASS / 1 WARN / 0 FAIL(중복좌표). 원자료 출처·기준연도·이용조건의 미확인 사항은 유지. 기존 사용자 Web GIS 변경과 루트 원자료는 편집·커밋하지 않음.
- 다음 작업: 이번 Markdown 원고를 제출 서식에 반영하고 5쪽 본문·별첨을 실제 렌더링으로 확인. 기존 DOCX는 이전 편집본이며 이번 수정 내용·페이지 검증이 반영되지 않았음. 좌표·현장자료·타 지역 재현 확인도 남아 있음.

## 2026-09-01

- Submission artifacts are now local-only: final DOCX and Markdown draft are stored under `docs/submission/`, ignored by Git. Reproducible analysis code, validation outputs, and the visualization manifest remain public repository candidates.

날짜별 작업 내역은 핵심 결과와 검증만 간단히 기록한다. 데이터 품질 이슈의 원인·영향·해결·잔여 위험은 [`docs/data-quality.md`](docs/data-quality.md)에서 관리한다.

## 2026-08-31

- `docs/data-quality.md` 신규 작성: 좌표 품질, SGIS 결측, 공식 인구격자 부재, VWorld snapshot·라이선스, 기준연도 및 통계 정의 차이를 상태·영향·검증 근거와 함께 기록.
- 해결된 인코딩·CRS/geometry·시설 ID/필수 필드 검증도 이력으로 보존.
- 현재 파이프라인 검증 상태 확인: 전체 `PASS`, `validation_report.json` 좌표 중복 WARN 1건, 제출근거 검증 `17 PASS / 0 WARN / 0 FAIL`.
- SGIS 연결 전후 정책 근거 비교 스크립트·산출물 추가: `analysis/build_sgis_policy_comparison.py`, `data/analysis/sgis_policy_comparison.csv/json`, `docs/sgis-policy-comparison.md`.
- 비교 결과: 전체 427개 중 SGIS 5분 175개, 10분 190개, 양쪽 모두 175개; 10분 상위 25% 플래그 49개, 5→10분 증가폭 상위 25% 플래그 44개.
- `validate_outputs.py` 결과 `PASS (16 PASS / 0 FAIL)`, 제출근거 검증 `PASS (17 PASS / 0 WARN / 0 FAIL)`. 이번 작업에서 새 데이터 품질 이슈는 발견되지 않아 `docs/data-quality.md`의 열린 이슈 5건은 유지.
- TODO 첫 화면을 제출 중심 상위 작업 7개로 압축하고, 기존 세부 체크리스트는 접힌 `NOW 상세 실행 체크리스트`로 이동해 보존.
- 427개 못의 `지역 특성·수요·접근성 → 활용 가능성 → 정책 방향` 해석표를 SGIS 근거 비교 문서에 추가. 정책 방향은 검토 가설로만 표시하고 현장자료 확인 전 확정하지 않음.
- 기존 산출물 검증: `policy_review_context` 6개 그룹은 427개·고유 ID 427개로 상호배타, `INSUFFICIENT_SGIS_10MIN` 190개는 다른 그룹과 중복 0개. 별도 SGIS flag는 중복 가능하며 양쪽 flag 중복 42개.
- 규칙기반 시설 분류는 427행·고유 ID 427개·그룹 합계 427개로 누락 없이 1개 라벨씩 연결됨. `validate_submission_claims.py`는 `17 PASS / 0 WARN / 0 FAIL`.
- 제출 보고서와 시각화 카탈로그 생성: `docs/submission/sgis-uiseong-submission-report.md`, `data/analysis/submission_visualization_manifest.json`. 제출 연결 그림 8개 모두 파일 존재·비어 있지 않음으로 확인. 제출 원고는 로컬 전용 경로로 관리.
- 보고서 상태는 `READY_WITH_DOCUMENTED_LIMITATIONS`; 좌표·SGIS 결측·공식 인구격자·VWorld 라이선스 한계를 명시하고, 현장자료 확인 전 정책 방향은 검토 가설로 제한.
- `build_submission_report.py` 실행 후 검증 수치: 시설 427개, SGIS 10분 응답 190개, 미확보 190개, 좌표 품질 제외 47개, VWorld 시설 68개·도로 483개. 제출근거 검증은 `17 PASS / 0 WARN / 0 FAIL`.
- 전체 `run_competition_pipeline.py` 재실행 후 보고서·시각화 카탈로그를 최신 산출물 기준으로 갱신. 파이프라인 `PASS`, validation `16 PASS / 0 FAIL`(좌표 중복 WARN 1건), 제출근거 `17 PASS / 0 WARN / 0 FAIL`.
- SGIS 활용 우수사례 공모전 양식에 맞춘 A4 5페이지 DOCX 제출 보고서 생성: `docs/submission/sgis-uiseong-excellent-use-case-submission.docx`. 제목·본문 글꼴/크기, 160% 줄간격, 여백, 표·그림·추진성과를 반영. 제출물은 공개 Git에서 제외.
- DOCX 구조 검증: 수동 페이지 나눔 4개(5페이지 구성), 이미지 4개, 표 헤더 2개, A4 210×297mm, 여백 상하 10mm·좌우 20mm, 머리·꼬리말 10mm. 접근성 감사 0건.
- DOCX PNG 렌더링은 환경의 `pdf2image` 및 LibreOffice 미설치로 완료하지 못함. 대신 OOXML 구조·지정 글꼴·페이지 나눔·이미지·표 헤더를 확인했으며, 최종 문서 상태는 제출용으로 보관.

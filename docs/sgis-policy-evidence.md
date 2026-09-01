# SGIS 기반 정책 근거 분석

이 문서는 SGIS 생활권역 인구와 기존 의성군 못·읍면·주변환경 자료를 연결한 기술통계형 정책 검토표다. 자동 추천점수나 정책 확정 결과가 아니다.

SGIS 연결 전후에 정책 검토 근거의 범위와 해석이 어떻게 달라지는지는 [`sgis-policy-comparison.md`](sgis-policy-comparison.md)에서 별도로 비교한다.

- 전체 못: `427`개
- 좌표 품질 검증 후 고유 좌표: `380`개
- 10분 인구 확보 고유 좌표: `190`개
- 5·10분 모두 확보 고유 좌표: `175`개

## 해석 기준

- `HIGH_10MIN_REACH`: 검증 좌표 중 10분 생활권 인구 상위 25%
- `HIGH_5_TO_10_EXPANSION`: 5분에서 10분으로 늘어난 인구 상위 25%
- `HIGH_ELDERLY_CONTEXT`·`HIGH_YOUTH_CONTEXT`: 기존 읍·면 행정통계 비율 상위 25%
- `NO_MAPPED_FACILITY_CONTEXT`: 현재 부분 VWorld 레이어에서 주변시설이 매핑되지 않은 맥락. 서비스 부족의 확정판정이 아님

## 10분 도달인구 상위 검토 후보

|   pond_id | emd_name   |   sgis_population_10min |   sgis_population_gain_5_to_10 | policy_evidence_flags                                                                 |
|----------:|:-----------|------------------------:|-------------------------------:|:--------------------------------------------------------------------------------------|
|       474 | 단북면     |                    3877 |                           1579 | HIGH_10MIN_REACH;HIGH_5_TO_10_EXPANSION                                               |
|       670 | 안계면     |                    3258 |                           2324 | HIGH_10MIN_REACH;HIGH_5_TO_10_EXPANSION;HIGH_YOUTH_CONTEXT                            |
|       660 | 단북면     |                    3037 |                           2517 | HIGH_10MIN_REACH;HIGH_5_TO_10_EXPANSION                                               |
|       662 | 단북면     |                    2803 |                           2180 | HIGH_10MIN_REACH;HIGH_5_TO_10_EXPANSION;NO_MAPPED_FACILITY_CONTEXT                    |
|       668 | 안계면     |                    1957 |                           1929 | HIGH_10MIN_REACH;HIGH_5_TO_10_EXPANSION;HIGH_YOUTH_CONTEXT;NO_MAPPED_FACILITY_CONTEXT |
|       475 | 안계면     |                    1704 |                           1490 | HIGH_10MIN_REACH;HIGH_5_TO_10_EXPANSION;HIGH_YOUTH_CONTEXT;NO_MAPPED_FACILITY_CONTEXT |
|       677 | 다인면     |                    1129 |                            690 | HIGH_10MIN_REACH;HIGH_5_TO_10_EXPANSION;HIGH_YOUTH_CONTEXT                            |
|       678 | 다인면     |                     979 |                            781 | HIGH_10MIN_REACH;HIGH_5_TO_10_EXPANSION;HIGH_YOUTH_CONTEXT                            |
|       667 | 단북면     |                     973 |                            610 | HIGH_10MIN_REACH;HIGH_5_TO_10_EXPANSION                                               |
|       477 | 안계면     |                     855 |                            792 | HIGH_10MIN_REACH;HIGH_5_TO_10_EXPANSION;HIGH_YOUTH_CONTEXT                            |

## 정책 검토 맥락별 건수

| context                    |   count |
|:---------------------------|--------:|
| INSUFFICIENT_SGIS_10MIN    |     190 |
| CONTEXT_ONLY               |      74 |
| COMMUNITY_SUPPORT_REVIEW   |      53 |
| FIELD_REVIEW_REQUIRED      |      47 |
| YOUTH_PARTICIPATION_REVIEW |      43 |
| ACCESS_AND_REACH_REVIEW    |      20 |

정책 검토 맥락이 부여된 검증 시설은 `116`개이며, 각 시설은 현장관리 상태·보존가치·실제 서비스 수요를 추가 확인해야 한다.

## 주의사항

- SGIS 생활권역 인구는 주민등록 인구격자나 500m·1km Buffer 인구로 명명하지 않는다.
- `DATA_NOT_AVAILABLE`, 대표점, 인근좌표, 중복좌표는 임의 보정·0명 대체·순위 편입을 하지 않는다.
- 10분 생활권은 시설 간 중첩되므로 시설별 값을 합산하지 않는다.
- 원자료와 기준은 `data/analysis/sgis_policy_evidence.json` 및 `data/manifests/sgis_sources.csv`에서 확인한다.
- 현장검토 입력은 `data/analysis/policy_candidate_review_template.csv`에서 작성한다. 빈 칸은 미확인 상태이며 추정값을 입력하지 않는다.

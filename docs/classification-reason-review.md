# classification_reason 표본 검토

기존 규칙기반 분류의 `classification_reason`가 실제 입력 필드와 일치하는지 유형별 대표 표본을 점검한 결과다. 이 검토는 재분류·가중치 적용·결측 보정을 수행하지 않는다.

- 전체 시설: `427`개
- D_PRESERVATION fallback: `329`개 (77.0%)
- 유형별 표본: `5`개(존재하는 유형 기준)
- 미대표 유형: `C_COMMUNITY, E_MANAGEMENT_PRIORITY`

## 유형별 전체 건수

| classification_type   |   facility_count |
|:----------------------|-----------------:|
| A_CULTURE_TOURISM     |               55 |
| B_ECO_EDUCATION       |               43 |
| C_COMMUNITY           |                0 |
| D_PRESERVATION        |              329 |
| E_MANAGEMENT_PRIORITY |                0 |

## 표본 검토 결과

|   pond_id | classification_type   | classification_reason                                                                                      | review_status   | review_detail                                                        |
|----------:|:----------------------|:-----------------------------------------------------------------------------------------------------------|:----------------|:---------------------------------------------------------------------|
|         1 | A_CULTURE_TOURISM     | 도로 37m 이내이며 1km 생활시설 13개                                                                        | PASS            | road <= 300m and mapped facility count > 0                           |
|        10 | A_CULTURE_TOURISM     | 도로 37m 이내이며 1km 생활시설 13개                                                                        | PASS            | road <= 300m and mapped facility count > 0                           |
|        11 | A_CULTURE_TOURISM     | 도로 37m 이내이며 1km 생활시설 13개                                                                        | PASS            | road <= 300m and mapped facility count > 0                           |
|        12 | A_CULTURE_TOURISM     | 도로 37m 이내이며 1km 생활시설 13개                                                                        | PASS            | road <= 300m and mapped facility count > 0                           |
|        13 | A_CULTURE_TOURISM     | 도로 37m 이내이며 1km 생활시설 13개                                                                        | PASS            | road <= 300m and mapped facility count > 0                           |
|       226 | B_ECO_EDUCATION       | 1km 농업지역 비율 상위 25%이고 도로 접근성이 낮음                                                          | PASS            | agricultural ratio Q3 and road > 500m                                |
|       227 | B_ECO_EDUCATION       | 1km 농업지역 비율 상위 25%이고 도로 접근성이 낮음                                                          | PASS            | agricultural ratio Q3 and road > 500m                                |
|       228 | B_ECO_EDUCATION       | 1km 농업지역 비율 상위 25%이고 도로 접근성이 낮음                                                          | PASS            | agricultural ratio Q3 and road > 500m                                |
|       383 | B_ECO_EDUCATION       | 1km 농업지역 비율 상위 25%이고 도로 접근성이 낮음                                                          | PASS            | agricultural ratio Q3 and road > 500m                                |
|       385 | B_ECO_EDUCATION       | 1km 농업지역 비율 상위 25%이고 도로 접근성이 낮음                                                          | PASS            | agricultural ratio Q3 and road > 500m                                |
|       100 | D_PRESERVATION        | 현재 확보된 자료만으로 활동형 판정에 필요한 인구·도로·생활시설 근거가 부족하여 보존·기록형으로 보수적 표시 | PASS            | conservative fallback reason explicitly states insufficient evidence |
|       101 | D_PRESERVATION        | 현재 확보된 자료만으로 활동형 판정에 필요한 인구·도로·생활시설 근거가 부족하여 보존·기록형으로 보수적 표시 | PASS            | conservative fallback reason explicitly states insufficient evidence |
|       102 | D_PRESERVATION        | 현재 확보된 자료만으로 활동형 판정에 필요한 인구·도로·생활시설 근거가 부족하여 보존·기록형으로 보수적 표시 | PASS            | conservative fallback reason explicitly states insufficient evidence |
|       103 | D_PRESERVATION        | 현재 확보된 자료만으로 활동형 판정에 필요한 인구·도로·생활시설 근거가 부족하여 보존·기록형으로 보수적 표시 | PASS            | conservative fallback reason explicitly states insufficient evidence |
|       188 | D_PRESERVATION        | 현재 확보된 자료만으로 활동형 판정에 필요한 인구·도로·생활시설 근거가 부족하여 보존·기록형으로 보수적 표시 | PASS            | conservative fallback reason explicitly states insufficient evidence |

## 해석 및 다음 조치

- 표본의 `PASS`는 해당 규칙의 입력 필드와 근거 문장이 맞는다는 뜻이며, 정책 타당성이나 현장 상태를 확정하지 않는다.
- D_PRESERVATION 비율은 보수적 fallback 결과다. 관리상태·보존가치·현장조사 자료를 추가하면 일부 유형은 달라질 수 있다.
- C_COMMUNITY와 E_MANAGEMENT_PRIORITY는 현재 분류 결과에 표본을 만들 수 없으므로, 해당 유형이 없다는 사실 자체를 결과로 기록한다.
- 수동 검토는 `data/analysis/policy_candidate_review_template.csv`와 함께 진행한다.

## 산출물

- `data/analysis/classification_reason_review.csv`
- `data/analysis/classification_reason_review.json`

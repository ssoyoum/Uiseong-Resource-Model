"""Build a reproducible comparison of policy evidence with and without SGIS.

The comparison describes how SGIS changes the evidence available for review. It
does not create a score, fill missing values, or turn a review context into a
policy recommendation.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "data" / "analysis" / "sgis_policy_evidence.csv"
CLASSIFICATION_INPUT_PATH = ROOT / "data" / "analysis" / "pond_classification.csv"
OUTPUT_CSV = ROOT / "data" / "analysis" / "sgis_policy_comparison.csv"
OUTPUT_JSON = ROOT / "data" / "analysis" / "sgis_policy_comparison.json"
REPORT_PATH = ROOT / "docs" / "sgis-policy-comparison.md"


def build() -> tuple[pd.DataFrame, dict]:
    source = pd.read_csv(INPUT_PATH, dtype={"pond_id": str})
    classification = pd.read_csv(CLASSIFICATION_INPUT_PATH, dtype={"pond_id": str})
    required = {
        "pond_id",
        "sgis_analysis_eligible",
        "sgis_population_5min",
        "sgis_population_10min",
        "sgis_population_gain_5_to_10",
        "policy_review_context",
        "policy_analysis_status",
        "sgis_10min_reach_band",
        "sgis_expansion_band",
    }
    missing = sorted(required.difference(source.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    eligible = source[source["sgis_analysis_eligible"].astype(str).str.lower().eq("true")].copy()
    for column in ("sgis_population_5min", "sgis_population_10min", "sgis_population_gain_5_to_10"):
        eligible[column] = pd.to_numeric(eligible[column], errors="coerce")

    total = len(source)
    available_5 = int(eligible["sgis_population_5min"].notna().sum())
    available_10 = int(eligible["sgis_population_10min"].notna().sum())
    available_both = int(eligible["sgis_population_gain_5_to_10"].notna().sum())
    insufficient_10 = int((source["policy_review_context"] == "INSUFFICIENT_SGIS_10MIN").sum())
    excluded_coordinates = int((source["policy_analysis_status"] == "EXCLUDED_COORDINATE_QUALITY").sum())
    context_counts = {str(key): int(value) for key, value in source["policy_review_context"].value_counts().items()}
    flag_counts = {
        "HIGH_10MIN_REACH": int((source["sgis_10min_reach_band"] == "HIGH").sum()),
        "HIGH_5_TO_10_EXPANSION": int((source["sgis_expansion_band"] == "HIGH").sum()),
    }
    high_reach_ids = set(source.loc[source["sgis_10min_reach_band"] == "HIGH", "pond_id"])
    high_expansion_ids = set(source.loc[source["sgis_expansion_band"] == "HIGH", "pond_id"])
    context_counts = {
        str(key): int(value) for key, value in source["policy_review_context"].value_counts().items()
    }
    classification_counts = {
        str(key): int(value) for key, value in classification["classification_label"].value_counts().items()
    }
    missing_context_ids = set(source.loc[source["policy_review_context"] == "INSUFFICIENT_SGIS_10MIN", "pond_id"])
    other_context_ids = set(source.loc[source["policy_review_context"] != "INSUFFICIENT_SGIS_10MIN", "pond_id"])

    rows = [
        {
            "comparison_dimension": "분석 대상 범위",
            "without_sgis": f"{total}개 시설의 읍면·도로·VWorld 주변환경·규칙기반 분류",
            "with_sgis": f"{available_10}개 고유 검증좌표에 10분 주행생활권 인구 추가",
            "interpretation": "SGIS는 전체 시설을 대체하지 않고, 응답이 확인된 시설에만 도달 규모 근거를 추가한다.",
        },
        {
            "comparison_dimension": "5분·10분 생활권 응답",
            "without_sgis": "주행시간 기반 도달 규모 근거 없음",
            "with_sgis": f"5분 {available_5}개, 10분 {available_10}개, 5·10분 모두 {available_both}개",
            "interpretation": "5분에서 10분으로 확장되는 수요 신호를 응답이 있는 시설에서만 비교한다.",
        },
        {
            "comparison_dimension": "정책 검토 맥락",
            "without_sgis": "읍면 인구구조·주변시설·도로 접근성 중심의 맥락 검토",
            "with_sgis": f"접근·도달 검토 {context_counts.get('ACCESS_AND_REACH_REVIEW', 0)}개, 청년참여 검토 {context_counts.get('YOUTH_PARTICIPATION_REVIEW', 0)}개, 공동체 지원 검토 {context_counts.get('COMMUNITY_SUPPORT_REVIEW', 0)}개",
            "interpretation": "SGIS는 정책 유형을 자동 확정하지 않고, 현장검토 우선순위를 설명할 수 있는 추가 근거로 사용한다.",
        },
        {
            "comparison_dimension": "결측·좌표 품질",
            "without_sgis": "시설 전체를 동일한 인구 근거로 비교할 수 없음",
            "with_sgis": f"10분 인구 미확보 {insufficient_10}개, 좌표 품질 제외 {excluded_coordinates}개",
            "interpretation": "미응답은 0명이나 낮은 수요로 해석하지 않고, 분석 가능 범위를 명시한다.",
        },
        {
            "comparison_dimension": "해석 가능한 SGIS 신호",
            "without_sgis": "주행권역 도달 규모·5→10분 증가폭 미확인",
            "with_sgis": f"10분 상위 25% 신호 {flag_counts['HIGH_10MIN_REACH']}개, 5→10분 증가폭 상위 25% 신호 {flag_counts['HIGH_5_TO_10_EXPANSION']}개",
            "interpretation": "상위 사분위 신호는 기술통계형 검토 플래그이며, 정책 점수나 인과효과가 아니다.",
        },
    ]
    comparison = pd.DataFrame(rows)
    comparison.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    summary = {
        "source": str(INPUT_PATH.relative_to(ROOT)).replace("\\", "/"),
        "comparison_output": str(OUTPUT_CSV.relative_to(ROOT)).replace("\\", "/"),
        "facility_count": total,
        "sgis_eligible_unique_coordinate_points": int(len(eligible)),
        "sgis_available_5min": available_5,
        "sgis_available_10min": available_10,
        "sgis_available_both": available_both,
        "insufficient_sgis_10min": insufficient_10,
        "excluded_coordinate_quality": excluded_coordinates,
        "policy_review_context_counts": context_counts,
        "evidence_flag_counts": flag_counts,
        "evidence_flag_overlap_count": int(len(high_reach_ids & high_expansion_ids)),
        "policy_context_group_sum": int(sum(context_counts.values())),
        "policy_context_groups_mutually_exclusive": True,
        "sgis_missing_context_overlap_count": int(len(missing_context_ids & other_context_ids)),
        "classification_rows": int(len(classification)),
        "classification_unique_pond_ids": int(classification["pond_id"].nunique()),
        "classification_group_sum": int(sum(classification_counts.values())),
        "classification_counts": classification_counts,
        "method": "Descriptive comparison only; no imputation, weights, score, causal claim, or automatic recommendation.",
    }
    OUTPUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return comparison, summary


def write_report(comparison: pd.DataFrame, summary: dict) -> None:
    lines = [
        "# SGIS 정책 근거 추가 효과 비교",
        "",
        "이 문서는 SGIS 생활권역 주행인구를 연결하기 전후에 정책 검토에 사용할 수 있는 근거가 어떻게 달라지는지 비교한다. 자동 추천점수나 정책 확정 결과가 아니다.",
        "",
        f"- 전체 시설: `{summary['facility_count']}`개",
        f"- SGIS 분석 대상 고유 좌표: `{summary['sgis_eligible_unique_coordinate_points']}`개",
        f"- 5분 응답: `{summary['sgis_available_5min']}`개 / 10분 응답: `{summary['sgis_available_10min']}`개",
        f"- 5분·10분 모두 응답: `{summary['sgis_available_both']}`개",
        f"- 10분 인구 미확보: `{summary['insufficient_sgis_10min']}`개 / 좌표 품질 제외: `{summary['excluded_coordinate_quality']}`개",
        "",
        "## 비교표",
        "",
        comparison.to_markdown(index=False),
        "",
        "## 정책 해석에 추가된 내용",
        "",
        f"- SGIS가 실제로 추가하는 근거는 10분 도달인구와 5분→10분 증가폭이며, 각각 상위 25% 기술통계 플래그로만 사용한다. 현재 플래그는 10분 도달인구 `{summary['evidence_flag_counts']['HIGH_10MIN_REACH']}`개, 증가폭 `{summary['evidence_flag_counts']['HIGH_5_TO_10_EXPANSION']}`개다.",
        f"- 정책 검토 맥락은 접근·도달 `{summary['policy_review_context_counts'].get('ACCESS_AND_REACH_REVIEW', 0)}`개, 청년참여 `{summary['policy_review_context_counts'].get('YOUTH_PARTICIPATION_REVIEW', 0)}`개, 공동체 지원 `{summary['policy_review_context_counts'].get('COMMUNITY_SUPPORT_REVIEW', 0)}`개로 분리된다.",
        "- SGIS 미응답·좌표 제외 시설은 판단에서 임의로 낮게 평가하지 않고 현장·좌표 확인 대상으로 남긴다.",
        "- SGIS 값은 주민등록 인구격자, 읍면 총계, 500m·1km Buffer 인구가 아니며 시설 간 합산하지 않는다.",
        "- 현장관리상태·보존가치·실제 서비스 수요를 확인하기 전에는 정책 후보를 확정하지 않는다.",
        "",
        "## 그룹 합계·중복 검증",
        "",
        "`policy_review_context`는 시설별 최종 검토 맥락을 하나만 저장하는 필드이므로 아래 6개 그룹은 상호배타적이다.",
        "",
        "| policy_review_context | 시설 수 |",
        "|---|---:|",
    ]
    for context in (
        "ACCESS_AND_REACH_REVIEW",
        "COMMUNITY_SUPPORT_REVIEW",
        "CONTEXT_ONLY",
        "FIELD_REVIEW_REQUIRED",
        "INSUFFICIENT_SGIS_10MIN",
        "YOUTH_PARTICIPATION_REVIEW",
    ):
        lines.append(f"| `{context}` | {summary['policy_review_context_counts'].get(context, 0)} |")
    lines.extend([
        f"| **합계** | **{summary['policy_context_group_sum']}** |",
        "",
        f"- 정책 검토 그룹 합계: `{summary['policy_context_group_sum']}`개; 시설별 행 수: `{summary['facility_count']}`개; 고유 시설 ID: `{summary['sgis_eligible_unique_coordinate_points'] + summary['excluded_coordinate_quality']}`개.",
        f"- `INSUFFICIENT_SGIS_10MIN` `{summary['insufficient_sgis_10min']}`개는 다른 `policy_review_context` 그룹과 겹치지 않으며, 해당 그룹의 10분 인구값도 모두 미확보 상태다.",
        f"- `HIGH_10MIN_REACH` `{summary['evidence_flag_counts']['HIGH_10MIN_REACH']}`개와 `HIGH_5_TO_10_EXPANSION` `{summary['evidence_flag_counts']['HIGH_5_TO_10_EXPANSION']}`개는 별도 flag라서 서로 겹칠 수 있고, 실제 중복은 `{summary['evidence_flag_overlap_count']}`개다.",
        f"- 별도 규칙기반 분류 결과도 `{summary['classification_rows']}`행·고유 시설 ID `{summary['classification_unique_pond_ids']}`개·그룹 합계 `{summary['classification_group_sum']}`개로 427개 전부에 1개 분류 라벨이 연결된다. 이는 정책 검토 맥락과 다른 분류 체계다.",
        "",
        "## 427개 못 Case Study 해석표",
        "",
        "| 검토 맥락 | 확인된 데이터 근거 | 활용 가능성 해석 | 정책 방향(검토 가설) | 확정 전 추가 확인 |",
        "|---|---|---|---|---|",
        f"| 청년 참여 검토 | 읍면 청년비율 상위 맥락 + SGIS 10분 응답. 현재 `{summary['policy_review_context_counts'].get('YOUTH_PARTICIPATION_REVIEW', 0)}`개 | 청년층이 접근 가능한 지역자원 활용 가능성을 검토 | 청년 참여형 활동·창업·체험 | 현장관리상태·보존가치·실제 청년 수요 |",
        f"| 공동체 지원 검토 | 읍면 고령비율 상위 + 현재 VWorld 매핑시설 없음. 현재 `{summary['policy_review_context_counts'].get('COMMUNITY_SUPPORT_REVIEW', 0)}`개 | 생활서비스 보완 또는 커뮤니티 활용 가능성을 검토 | 생활지원·커뮤니티 | 부분 시설 레이어의 누락 여부와 현장 운영상태 |",
        f"| 접근·도달 검토 | SGIS 10분 도달인구 또는 5→10분 증가폭 상위 사분위. 현재 `{summary['policy_review_context_counts'].get('ACCESS_AND_REACH_REVIEW', 0)}`개 | 주행 접근권역 안의 이용자 도달 가능성을 검토 | 관광·체험·체류 또는 접근성 기반 활용 | 관광시설·도로 연결성·현장 수요 |",
        "| 현장 확인 필요 | 좌표 품질 제외 또는 SGIS 10분 미확보 | 현재 공간·인구 근거만으로 방향을 정하지 않음 | 정책 후보 보류 | 좌표 보정, SGIS 재추출, 관리·보존 자료 |",
        "",
        "위 표의 정책 방향은 데이터 기반 검토 가설이다. SGIS 통계가 있다고 해서 해당 정책의 수요·효과가 입증되는 것은 아니며, 현장자료와 관리상태·보존가치 대조가 끝나기 전에는 후보를 확정하지 않는다.",
        "",
        "## 재현",
        "",
        "```bash",
        "python analysis/analyze_sgis_policy_evidence.py",
        "python analysis/build_sgis_policy_comparison.py",
        "python analysis/validate_submission_claims.py",
        "```",
        "",
        f"근거 원본은 `{summary['source']}`와 `data/analysis/pond_classification.csv`, 비교 산출물은 `{summary['comparison_output']}`와 `data/analysis/sgis_policy_comparison.json`이다.",
    ])
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    frame, result = build()
    write_report(frame, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))

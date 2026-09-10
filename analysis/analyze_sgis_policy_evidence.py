"""Create a descriptive SGIS-to-policy evidence table for the 427 ponds.

This is an evidence-screening step, not a weighted recommendation model. It
uses distribution bands and explicit caveats so a policy direction can be
reviewed against the underlying data and field conditions.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "data" / "analysis" / "sgis_catchment_analysis.csv"
OUTPUT_CSV = ROOT / "data" / "analysis" / "sgis_policy_evidence.csv"
OUTPUT_JSON = ROOT / "data" / "analysis" / "sgis_policy_evidence.json"
REVIEW_TEMPLATE_CSV = ROOT / "data" / "analysis" / "policy_candidate_review_template.csv"
REPORT_PATH = ROOT / "docs" / "sgis-policy-evidence.md"


def numeric(frame: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(frame[column], errors="coerce")


def band(value: float, lower: float, upper: float) -> str:
    if value >= upper:
        return "HIGH"
    if value < lower:
        return "LOW"
    return "MID"


def quantiles(frame: pd.DataFrame, column: str) -> dict[str, float | None]:
    values = numeric(frame, column).dropna()
    if values.empty:
        return {"q25": None, "q75": None}
    return {"q25": float(values.quantile(0.25)), "q75": float(values.quantile(0.75))}


def build() -> tuple[pd.DataFrame, dict]:
    source = pd.read_csv(INPUT_PATH, dtype={"pond_id": str})
    required = {
        "pond_id",
        "emd_name",
        "sgis_analysis_eligible",
        "coordinate_group_id",
        "sgis_population_5min",
        "sgis_population_10min",
        "sgis_population_gain_5_to_10",
        "emd_youth_ratio",
        "emd_elderly_ratio",
        "facility_count_1000m",
        "accessibility_class",
    }
    missing = sorted(required.difference(source.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    source["sgis_analysis_eligible"] = source["sgis_analysis_eligible"].astype(str).str.lower().eq("true")
    source["sgis_population_5min"] = numeric(source, "sgis_population_5min")
    source["sgis_population_10min"] = numeric(source, "sgis_population_10min")
    source["sgis_population_gain_5_to_10"] = numeric(source, "sgis_population_gain_5_to_10")
    source["emd_youth_ratio"] = numeric(source, "emd_youth_ratio")
    source["emd_elderly_ratio"] = numeric(source, "emd_elderly_ratio")
    source["facility_count_1000m"] = numeric(source, "facility_count_1000m")

    # Inferential summaries use one row per valid coordinate point. All 427
    # facilities remain in the output, with excluded rows explicitly marked.
    eligible = source[source["sgis_analysis_eligible"]].drop_duplicates(
        "coordinate_group_id", keep="first"
    ).copy()
    eligible_10 = eligible[eligible["sgis_population_10min"].notna()].copy()
    eligible_both = eligible[eligible["sgis_population_gain_5_to_10"].notna()].copy()
    thresholds = {
        "sgis_population_10min": quantiles(eligible_10, "sgis_population_10min"),
        "sgis_population_gain_5_to_10": quantiles(eligible_both, "sgis_population_gain_5_to_10"),
        "emd_elderly_ratio": quantiles(eligible, "emd_elderly_ratio"),
        "emd_youth_ratio": quantiles(eligible, "emd_youth_ratio"),
        "facility_count_1000m": quantiles(eligible, "facility_count_1000m"),
    }

    output = source[[
        "pond_id", "address", "region", "emd_name", "coordinate_group_id", "coordinate_group_size", "coordinate_validation",
        "sgis_analysis_eligible", "sgis_population_5min", "sgis_population_10min",
        "sgis_population_gain_5_to_10", "sgis_population_10min_rank_pct",
        "emd_total_population", "emd_youth_ratio", "emd_elderly_ratio",
        "emd_population_change", "facility_count_1000m", "accessibility_class",
    ]].copy()
    output["policy_analysis_status"] = np.where(
        ~output["sgis_analysis_eligible"],
        "EXCLUDED_COORDINATE_QUALITY",
        np.where(output["sgis_population_10min"].notna(), "DESCRIPTIVE_EVIDENCE", "INSUFFICIENT_SGIS_10MIN"),
    )
    output["sgis_10min_reach_band"] = "DATA_NOT_AVAILABLE"
    output["sgis_expansion_band"] = "DATA_NOT_AVAILABLE"
    output["community_context"] = "DATA_NOT_AVAILABLE"
    output["mapped_facility_context"] = "DATA_NOT_AVAILABLE"
    output["policy_evidence_flags"] = ""
    output["policy_review_context"] = "FIELD_REVIEW_REQUIRED"

    eligible_ids = set(eligible["pond_id"])
    for index, row in output.iterrows():
        if row["pond_id"] not in eligible_ids:
            continue
        if pd.isna(row["sgis_population_10min"]):
            output.at[index, "policy_review_context"] = "INSUFFICIENT_SGIS_10MIN"
            continue
        flags: list[str] = []
        reach = row["sgis_population_10min"]
        if pd.notna(reach) and thresholds["sgis_population_10min"]["q25"] is not None:
            output.at[index, "sgis_10min_reach_band"] = band(
                float(reach),
                float(thresholds["sgis_population_10min"]["q25"]),
                float(thresholds["sgis_population_10min"]["q75"]),
            )
            if output.at[index, "sgis_10min_reach_band"] == "HIGH":
                flags.append("HIGH_10MIN_REACH")

        gain = row["sgis_population_gain_5_to_10"]
        if pd.notna(gain) and thresholds["sgis_population_gain_5_to_10"]["q25"] is not None:
            output.at[index, "sgis_expansion_band"] = band(
                float(gain),
                float(thresholds["sgis_population_gain_5_to_10"]["q25"]),
                float(thresholds["sgis_population_gain_5_to_10"]["q75"]),
            )
            if output.at[index, "sgis_expansion_band"] == "HIGH":
                flags.append("HIGH_5_TO_10_EXPANSION")

        elderly = row["emd_elderly_ratio"]
        youth = row["emd_youth_ratio"]
        elderly_q = thresholds["emd_elderly_ratio"]
        youth_q = thresholds["emd_youth_ratio"]
        if pd.notna(elderly) and elderly_q["q75"] is not None and elderly >= elderly_q["q75"]:
            output.at[index, "community_context"] = "ELDERLY_HIGH"
            flags.append("HIGH_ELDERLY_CONTEXT")
        elif pd.notna(youth) and youth_q["q75"] is not None and youth >= youth_q["q75"]:
            output.at[index, "community_context"] = "YOUTH_HIGH"
            flags.append("HIGH_YOUTH_CONTEXT")
        elif pd.notna(elderly) or pd.notna(youth):
            output.at[index, "community_context"] = "GENERAL_EMD_CONTEXT"

        facility_count = row["facility_count_1000m"]
        facility_q = thresholds["facility_count_1000m"]
        if pd.notna(facility_count) and facility_q["q25"] is not None:
            output.at[index, "mapped_facility_context"] = (
                "MAPPED_FACILITY_SPARSE" if facility_count <= facility_q["q25"] else "MAPPED_FACILITY_PRESENT"
            )
            if facility_count == 0:
                output.at[index, "mapped_facility_context"] = "NO_MAPPED_FACILITY_CONTEXT"
                flags.append("NO_MAPPED_FACILITY_CONTEXT")

        output.at[index, "policy_evidence_flags"] = ";".join(flags) or "NO_TOP_QUARTILE_SIGNAL"
        if "HIGH_ELDERLY_CONTEXT" in flags and "NO_MAPPED_FACILITY_CONTEXT" in flags:
            output.at[index, "policy_review_context"] = "COMMUNITY_SUPPORT_REVIEW"
        elif "HIGH_YOUTH_CONTEXT" in flags:
            output.at[index, "policy_review_context"] = "YOUTH_PARTICIPATION_REVIEW"
        elif "HIGH_10MIN_REACH" in flags or "HIGH_5_TO_10_EXPANSION" in flags:
            output.at[index, "policy_review_context"] = "ACCESS_AND_REACH_REVIEW"
        else:
            output.at[index, "policy_review_context"] = "CONTEXT_ONLY"

    output.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    review = output[
        (output["policy_analysis_status"] == "DESCRIPTIVE_EVIDENCE")
        & (output["policy_review_context"] != "CONTEXT_ONLY")
    ].copy()
    for column in (
        "management_status",
        "survey_status",
        "heritage_note",
        "field_photo_ref",
        "field_survey_date",
        "reviewer",
        "review_source",
        "review_note",
    ):
        review[column] = ""
    review["manual_review_status"] = "PENDING_MANUAL_REVIEW"
    review.to_csv(REVIEW_TEMPLATE_CSV, index=False, encoding="utf-8-sig")
    summary = {
        "source": str(INPUT_PATH.relative_to(ROOT)).replace("\\", "/"),
        "output": str(OUTPUT_CSV.relative_to(ROOT)).replace("\\", "/"),
        "review_template": str(REVIEW_TEMPLATE_CSV.relative_to(ROOT)).replace("\\", "/"),
        "facility_count": int(len(source)),
        "eligible_unique_coordinate_points": int(len(eligible)),
        "eligible_with_10min_population": int(len(eligible_10)),
        "eligible_with_5_and_10min_population": int(len(eligible_both)),
        "manual_review_candidate_count": int(len(review)),
        "thresholds_q25_q75": thresholds,
        "policy_review_context_counts": {
            str(key): int(value) for key, value in output["policy_review_context"].value_counts().items()
        },
        "evidence_flag_counts": {
            str(flag): int(output["policy_evidence_flags"].str.contains(flag, regex=False).sum())
            for flag in (
                "HIGH_10MIN_REACH",
                "HIGH_5_TO_10_EXPANSION",
                "HIGH_ELDERLY_CONTEXT",
                "HIGH_YOUTH_CONTEXT",
                "NO_MAPPED_FACILITY_CONTEXT",
            )
        },
        "method": "Descriptive quartile bands and explicit evidence flags; no weights, score, causal claim, or automatic policy recommendation.",
        "caveats": [
            "SGIS 5/10-minute values are route-based service-area population, not resident grid population.",
            "The EMD youth/elderly context is based on the existing MOIS 2025 administrative summary, not an SGIS regional API response.",
            "Mapped facility context reflects the partial VWorld facility layer and is not a complete service shortage measure.",
            "Duplicate, administrative representative, and nearby coordinates remain excluded until source coordinates are verified.",
        ],
    }
    OUTPUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output, summary


def write_report(output: pd.DataFrame, summary: dict) -> None:
    eligible = output[output["policy_analysis_status"] == "DESCRIPTIVE_EVIDENCE"].copy()
    top_reach = eligible.sort_values("sgis_population_10min", ascending=False).head(10)
    top_review = eligible[eligible["policy_review_context"] != "CONTEXT_ONLY"].copy()
    lines = [
        "# SGIS 기반 정책 근거 분석",
        "",
        "이 문서는 SGIS 생활권역 인구와 기존 의성군 못·읍면·주변환경 자료를 연결한 기술통계형 정책 검토표다. 자동 추천점수나 정책 확정 결과가 아니다.",
        "",
        "SGIS 연결 전후에 정책 검토 근거의 범위와 해석이 어떻게 달라지는지는 [`sgis-policy-comparison.md`](sgis-policy-comparison.md)에서 별도로 비교한다.",
        "",
        f"- 전체 못: `{summary['facility_count']}`개",
        f"- 좌표 품질 검증 후 고유 좌표: `{summary['eligible_unique_coordinate_points']}`개",
        f"- 10분 인구 확보 고유 좌표: `{summary['eligible_with_10min_population']}`개",
        f"- 5·10분 모두 확보 고유 좌표: `{summary['eligible_with_5_and_10min_population']}`개",
        "",
        "## 해석 기준",
        "",
        "- `HIGH_10MIN_REACH`: 검증 좌표 중 10분 생활권 인구 상위 25%",
        "- `HIGH_5_TO_10_EXPANSION`: 5분에서 10분으로 늘어난 인구 상위 25%",
        "- `HIGH_ELDERLY_CONTEXT`·`HIGH_YOUTH_CONTEXT`: 기존 읍·면 행정통계 비율 상위 25%",
        "- `NO_MAPPED_FACILITY_CONTEXT`: 현재 부분 VWorld 레이어에서 주변시설이 매핑되지 않은 맥락. 서비스 부족의 확정판정이 아님",
        "",
        "## 10분 도달인구 상위 검토 후보",
        "",
        top_reach[["pond_id", "emd_name", "sgis_population_10min", "sgis_population_gain_5_to_10", "policy_evidence_flags"]].to_markdown(index=False) if not top_reach.empty else "자료 없음",
        "",
        "## 정책 검토 맥락별 건수",
        "",
        pd.Series(summary["policy_review_context_counts"], name="count").rename_axis("context").to_frame().to_markdown(),
        "",
        f"정책 검토 맥락이 부여된 검증 시설은 `{len(top_review)}`개이며, 각 시설은 현장관리 상태·보존가치·실제 서비스 수요를 추가 확인해야 한다.",
        "",
        "## 주의사항",
        "",
        "- SGIS 생활권역 인구는 주민등록 인구격자나 500m·1km Buffer 인구로 명명하지 않는다.",
        "- `DATA_NOT_AVAILABLE`, 대표점, 인근좌표, 중복좌표는 임의 보정·0명 대체·순위 편입을 하지 않는다.",
        "- 10분 생활권은 시설 간 중첩되므로 시설별 값을 합산하지 않는다.",
        "- 원자료와 기준은 `data/analysis/sgis_policy_evidence.json` 및 `data/manifests/sgis_sources.csv`에서 확인한다.",
        "- 현장검토 입력은 `data/analysis/policy_candidate_review_template.csv`에서 작성한다. 빈 칸은 미확인 상태이며 추정값을 입력하지 않는다.",
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    frame, result = build()
    write_report(frame, result)
    print(json.dumps(result["policy_review_context_counts"], ensure_ascii=False, indent=2))

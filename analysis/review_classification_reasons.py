"""Review representative classification reasons against their input fields.

The report is a quality check for the existing rule-based classification. It
does not relabel facilities, add weights, or infer missing management data.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "data" / "analysis" / "pond_classification.csv"
OUTPUT_CSV = ROOT / "data" / "analysis" / "classification_reason_review.csv"
OUTPUT_JSON = ROOT / "data" / "analysis" / "classification_reason_review.json"
REPORT_PATH = ROOT / "docs" / "classification-reason-review.md"

EXPECTED_TYPES = (
    "A_CULTURE_TOURISM",
    "B_ECO_EDUCATION",
    "C_COMMUNITY",
    "D_PRESERVATION",
    "E_MANAGEMENT_PRIORITY",
)


def number(frame: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(frame[column], errors="coerce")


def check_reason(row: pd.Series, agriculture_q3: float | None) -> tuple[str, str]:
    classification = str(row.get("classification_type", ""))
    reason = str(row.get("classification_reason", ""))
    road = pd.to_numeric(row.get("nearest_road_m"), errors="coerce")
    facility_count = pd.to_numeric(row.get("facility_count_1000m"), errors="coerce")
    agriculture = pd.to_numeric(row.get("agricultural_ratio_1000m"), errors="coerce")
    elderly = pd.to_numeric(row.get("elderly_population_1000m"), errors="coerce")
    management = str(row.get("management", ""))

    if not reason or reason in {"nan", "None"}:
        return "FAIL", "classification_reason is empty"
    if classification == "A_CULTURE_TOURISM":
        supported = pd.notna(road) and pd.notna(facility_count) and road <= 300 and facility_count > 0
        return ("PASS", "road <= 300m and mapped facility count > 0" if supported else "REVIEW: A rule inputs not satisfied") if "도로" in reason and "생활시설" in reason else ("REVIEW", "A reason text does not name both rule inputs")
    if classification == "B_ECO_EDUCATION":
        supported = agriculture_q3 is not None and pd.notna(agriculture) and agriculture >= agriculture_q3 and pd.notna(road) and road > 500
        return ("PASS", "agricultural ratio Q3 and road > 500m" if supported else "REVIEW: B rule inputs not satisfied") if "농업지역" in reason and "접근성" in reason else ("REVIEW", "B reason text does not name both rule inputs")
    if classification == "C_COMMUNITY":
        supported = pd.notna(elderly) and pd.notna(road) and road <= 300
        return ("PASS", "elderly demand and road <= 300m" if supported else "REVIEW: C rule inputs not satisfied") if "고령인구" in reason and "접근성" in reason else ("REVIEW", "C reason text does not name both rule inputs")
    if classification == "D_PRESERVATION":
        return ("PASS", "conservative fallback reason explicitly states insufficient evidence") if "근거가 부족" in reason else ("REVIEW", "D reason does not state insufficient evidence")
    if classification == "E_MANAGEMENT_PRIORITY":
        supported = management.lower() in {"bad", "poor", "불량", "미흡"}
        return ("PASS", "management field matches priority rule" if supported else "REVIEW: management field not in priority values") if "관리상태" in reason else ("REVIEW", "E reason does not name management status")
    return "FAIL", "unknown classification type"


def run(sample_size: int = 5) -> dict:
    frame = pd.read_csv(INPUT_PATH, dtype={"id": str})
    required = {"id", "classification_type", "classification_label", "classification_reason"}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
    agriculture = number(frame, "agricultural_ratio_1000m")
    agriculture_q3 = float(agriculture.quantile(0.75)) if agriculture.notna().any() else None

    records: list[dict] = []
    sample_counts: dict[str, int] = {}
    for classification in EXPECTED_TYPES:
        subset = frame[frame["classification_type"].eq(classification)].sort_values("id").head(sample_size)
        sample_counts[classification] = int(len(subset))
        for _, row in subset.iterrows():
            status, detail = check_reason(row, agriculture_q3)
            records.append(
                {
                    "pond_id": str(row.get("id")),
                    "classification_type": classification,
                    "classification_label": row.get("classification_label"),
                    "classification_reason": row.get("classification_reason"),
                    "nearest_road_m": row.get("nearest_road_m"),
                    "facility_count_1000m": row.get("facility_count_1000m"),
                    "agricultural_ratio_1000m": row.get("agricultural_ratio_1000m"),
                    "elderly_population_1000m": row.get("elderly_population_1000m"),
                    "management": row.get("management"),
                    "review_status": status,
                    "review_detail": detail,
                }
            )
    review = pd.DataFrame(records)
    review.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    type_counts = frame["classification_type"].value_counts().to_dict()
    fallback_count = int(type_counts.get("D_PRESERVATION", 0))
    review_counts = review["review_status"].value_counts().to_dict() if not review.empty else {}
    summary = {
        "input": str(INPUT_PATH.relative_to(ROOT)).replace("\\", "/"),
        "output": str(OUTPUT_CSV.relative_to(ROOT)).replace("\\", "/"),
        "facility_count": int(len(frame)),
        "classification_counts": {classification: int(type_counts.get(classification, 0)) for classification in EXPECTED_TYPES},
        "fallback": {
            "type": "D_PRESERVATION",
            "count": fallback_count,
            "ratio": fallback_count / len(frame) if len(frame) else None,
        },
        "sample_size_per_type": sample_size,
        "sample_counts": sample_counts,
        "review_status_counts": {str(key): int(value) for key, value in review_counts.items()},
        "unrepresented_types": [classification for classification in EXPECTED_TYPES if type_counts.get(classification, 0) == 0],
        "agricultural_ratio_q3": agriculture_q3,
        "method": "Representative deterministic samples checked against existing rule inputs; no relabeling or imputation.",
        "interpretation": "A high D_PRESERVATION ratio indicates missing or insufficient inputs under the conservative rule, not that all facilities have been proven preservation priorities.",
    }
    OUTPUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def write_report(summary: dict) -> None:
    review = pd.read_csv(OUTPUT_CSV, dtype={"pond_id": str})
    lines = [
        "# classification_reason 표본 검토",
        "",
        "기존 규칙기반 분류의 `classification_reason`가 실제 입력 필드와 일치하는지 유형별 대표 표본을 점검한 결과다. 이 검토는 재분류·가중치 적용·결측 보정을 수행하지 않는다.",
        "",
        f"- 전체 시설: `{summary['facility_count']}`개",
        f"- D_PRESERVATION fallback: `{summary['fallback']['count']}`개 ({summary['fallback']['ratio']:.1%})",
        f"- 유형별 표본: `{summary['sample_size_per_type']}`개(존재하는 유형 기준)",
        f"- 미대표 유형: `{', '.join(summary['unrepresented_types']) if summary['unrepresented_types'] else '없음'}`",
        "",
        "## 유형별 전체 건수",
        "",
        pd.Series(summary["classification_counts"], name="facility_count").rename_axis("classification_type").to_frame().to_markdown(),
        "",
        "## 표본 검토 결과",
        "",
        review[["pond_id", "classification_type", "classification_reason", "review_status", "review_detail"]].to_markdown(index=False) if not review.empty else "표본 없음",
        "",
        "## 해석 및 다음 조치",
        "",
        "- 표본의 `PASS`는 해당 규칙의 입력 필드와 근거 문장이 맞는다는 뜻이며, 정책 타당성이나 현장 상태를 확정하지 않는다.",
        "- D_PRESERVATION 비율은 보수적 fallback 결과다. 관리상태·보존가치·현장조사 자료를 추가하면 일부 유형은 달라질 수 있다.",
        "- C_COMMUNITY와 E_MANAGEMENT_PRIORITY는 현재 분류 결과에 표본을 만들 수 없으므로, 해당 유형이 없다는 사실 자체를 결과로 기록한다.",
        "- 수동 검토는 `data/analysis/policy_candidate_review_template.csv`와 함께 진행한다.",
        "",
        "## 산출물",
        "",
        f"- `{summary['output']}`",
        "- `data/analysis/classification_reason_review.json`",
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    result = run()
    write_report(result)
    print(json.dumps(result["review_status_counts"], ensure_ascii=False, indent=2))

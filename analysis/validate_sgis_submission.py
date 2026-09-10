"""Audit the local SGIS draft against saved rows, summaries and figure inputs.

This checks explicit numerical claims and provenance, not field accuracy,
policy effectiveness, remote URL availability or word-processor pagination.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "docs/submission/sgis-uiseong-final-draft.md"
POLICY_LABELS = {
    "현장 확인 필요": "FIELD_REVIEW_REQUIRED",
    "SGIS 10분 인구 미확보": "INSUFFICIENT_SGIS_10MIN",
    "공동체 지원 검토": "COMMUNITY_SUPPORT_REVIEW",
    "청년참여 검토": "YOUTH_PARTICIPATION_REVIEW",
    "접근·도달 검토": "ACCESS_AND_REACH_REVIEW",
    "맥락 참고": "CONTEXT_ONLY",
}
TYPE_LABELS = {
    "보존·기록형": "D_PRESERVATION",
    "문화·관광형": "A_CULTURE_TOURISM",
    "생태·교육형": "B_ECO_EDUCATION",
}


def check(name, passed, **details):
    return {"name": f"sgis_submission:{name}", "status": "PASS" if passed else "FAIL", "details": details}


def json_file(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def table_claim(text, label, expected):
    values = re.findall(r"^\|\s*" + re.escape(label) + r"\s*\|\s*([\d,]+)\s*\|", text, re.M)
    actual = [int(value.replace(",", "")) for value in values]
    return check(f"table:{label}", actual == [int(expected)], expected=int(expected), actual=actual)


def number_claim(text, name, pattern, expected):
    actual = [float(value.replace(",", "")) for value in re.findall(pattern, text)]
    return check(name, bool(actual) and all(value == float(expected) for value in actual), expected=float(expected), actual=actual)


def markdown_links(paths):
    errors = []
    count = 0
    for path in paths:
        text = re.sub(r"```.*?```", "", path.read_text(encoding="utf-8"), flags=re.S)
        for match in re.finditer(r"!?\[[^\]]*\]\((<[^>]+>|[^\s)]+)(?:\s+\"[^\"]*\")?\)", text):
            target = match.group(1).strip("<>")
            parts = urlsplit(target)
            count += 1
            if parts.scheme:
                valid = parts.scheme in {"https", "http", "mailto"} and bool(parts.netloc or parts.scheme == "mailto")
            else:
                # File paths are checked; heading anchors are outside this check.
                valid = not parts.path or (path.parent / unquote(parts.path)).exists()
            if not valid:
                errors.append({"document": str(path.relative_to(ROOT)), "target": target})
    return check("markdown_paths_and_url_format", not errors, links_checked=count, errors=errors,
                 scope="Local paths and external URL format; no HTTP or heading-anchor check")


def figure_cohort_check(figure, paired):
    actual = list(map(str, figure.get("plotted_pond_ids", [])))
    expected = set(paired["pond_id"].astype(str))
    return check("scatter_cohort", len(actual) == len(expected) and set(actual) == expected
                 and figure.get("paired_count") == len(expected),
                 expected_count=len(expected), actual_count=len(actual),
                 unexpected_ids=sorted(set(actual) - expected), missing_ids=sorted(expected - set(actual)))


def validate_draft():
    text = DRAFT.read_text(encoding="utf-8")
    frame = pd.read_csv(ROOT / "data/analysis/sgis_catchment_analysis.csv", dtype={"pond_id": str})
    eligible_flag = frame["sgis_analysis_eligible"].astype(str).str.lower()
    if not eligible_flag.isin(["true", "false"]).all():
        raise ValueError("Invalid sgis_analysis_eligible values")
    eligible = frame[eligible_flag.eq("true")].drop_duplicates("coordinate_group_id")
    paired = eligible.dropna(subset=["sgis_population_5min", "sgis_population_10min"])
    available_10 = eligible["sgis_population_10min"].notna().sum()
    summary = json_file("data/analysis/sgis_catchment_analysis.json")
    policy = pd.read_csv(ROOT / "data/analysis/sgis_policy_evidence.csv", dtype={"pond_id": str})
    types = pd.read_csv(ROOT / "data/analysis/pond_classification.csv", dtype={"pond_id": str})
    raw = pd.read_csv(ROOT / "data/processed/population/sgis_drive_population.csv", dtype={"pond_id": str})
    population = pd.read_csv(ROOT / "data/processed/population/uiseong_population.csv")
    vworld = json_file("data/analysis/vworld_input_status.json")
    evidence = json_file("data/analysis/sgis_policy_evidence.json")
    counts = policy["policy_review_context"].value_counts().to_dict()
    type_counts = types["classification_type"].value_counts().to_dict()
    tables = {
        "분석 목록": len(frame), "좌표 품질 조건 통과": len(eligible),
        "5분 인구 확보": eligible["sgis_population_5min"].notna().sum(),
        "10분 인구 확보": available_10, "5분·10분 모두 확보": len(paired),
        "10분 인구 미확보": len(eligible) - available_10,
        **{label: counts.get(code, 0) for label, code in POLICY_LABELS.items()},
        **{label: type_counts.get(code, 0) for label, code in TYPE_LABELS.items()},
    }
    checks = [table_claim(text, label, expected) for label, expected in tables.items()]
    ids = set(frame["pond_id"])
    checks.append(check("facility_id_joins", frame["pond_id"].is_unique and all(
        source["pond_id"].is_unique and set(source["pond_id"]) == ids for source in [policy, types]),
        facility_count=len(frame)))
    checks.append(check("summary_cohorts", summary["facility_count"] == len(frame)
                        and summary["coordinate_quality"]["reliable_unique_points"] == len(eligible)
                        and summary["coverage"]["available_both"] == len(paired)
                        and summary["coverage"]["available_10min"] == int(available_10)
                        and evidence["policy_review_context_counts"] == counts))
    raw_values = raw.pivot(index="pond_id", columns="drive_time_min", values="sgis_population")
    joined_values = frame.set_index("pond_id")
    same_values = set(raw_values.index) == ids
    for minutes in [5, 10]:
        left = raw_values[minutes].reindex(joined_values.index)
        right = joined_values[f"sgis_population_{minutes}min"]
        same_values = same_values and (left.eq(right) | (left.isna() & right.isna())).all()
    checks.append(check("saved_response_values", same_values, response_rows=len(raw)))
    unlocated = raw["error"].fillna("").str.contains("unlocated", case=False, regex=False)
    no_population = raw["sgis_population"].isna() & ~unlocated
    flags = policy["policy_evidence_flags"].fillna("")
    reach = flags.str.contains("HIGH_10MIN_REACH", regex=False)
    gain = flags.str.contains("HIGH_5_TO_10_EXPANSION", regex=False)
    q_reach = eligible["sgis_population_10min"].quantile(.75)
    q_gain = (paired["sgis_population_10min"] - paired["sgis_population_5min"]).quantile(.75)
    total = population["total_population"].sum()
    change = population["population_change"].sum()
    numeric_claims = [
        ("population_2024", r"2024년 12월 ([\d,]+)명", total - change),
        ("population_2025", r"2025년 12월 ([\d,]+)명", total),
        ("population_decrease", r"명으로 ([\d,]+)명 감소", -change),
        ("road_objects", r"UQ151 도로 객체 (\d+)개", vworld["road_feature_count"]),
        ("facility_objects", r"UQ164·UO601 시설 객체 (\d+)개", vworld["facility_count"]),
        ("reach_flag", r"10분 인구의 제3사분위수 이상에 해당하는 못은 (\d+)개", int(reach.sum())),
        ("gain_flag", r"증가폭의 제3사분위수 이상은 (\d+)개", int(gain.sum())),
        ("flag_overlap", r"두 조건을 동시에 만족하는 못은 (\d+)개", int((reach & gain).sum())),
        ("reach_threshold", r"10분 인구의 상위 기준은 \d+개 응답의 제3사분위수인 \*\*([\d.]+)명 이상", float(q_reach)),
        ("gain_threshold", r"증가폭은 \d+개 응답의 제3사분위수인 \*\*([\d.]+)명 이상", float(q_gain)),
        ("raw_requests", r"총 (\d+)개 요청행", len(raw)),
        ("raw_missing", r"인구 미확보는 (\d+)행", int(raw["sgis_population"].isna().sum())),
        ("raw_5min", r"원수집 결과는 5분 (\d+)개", int(raw.loc[raw["drive_time_min"].eq(5), "sgis_population"].notna().sum())),
        ("raw_10min", r"원수집 결과는 5분 \d+개·10분 (\d+)개", int(raw.loc[raw["drive_time_min"].eq(10), "sgis_population"].notna().sum())),
        ("unlocated_rows", r"이 중 (\d+)행은", int(unlocated.sum())),
        ("unlocated_facilities", r"행은 (\d+)개 못에서 발생한 위치 인식 실패", int(raw.loc[unlocated, "pond_id"].nunique())),
        ("no_population_rows", r"나머지 (\d+)행은 5분 권역", int(no_population.sum())),
        ("unique_coordinates", r"고유 좌표는 (\d+)곳", int(frame["coordinate_group_id"].nunique())),
    ]
    for name, pattern, expected in numeric_claims:
        checks.append(number_claim(text, name, pattern, expected))
    review = pd.read_csv(ROOT / "data/analysis/policy_candidate_review_template.csv", dtype={"pond_id": str})
    candidate_ids = set(policy.loc[policy["policy_review_context"].isin([
        "ACCESS_AND_REACH_REVIEW", "YOUTH_PARTICIPATION_REVIEW", "COMMUNITY_SUPPORT_REVIEW"]), "pond_id"])
    checks.append(check("review_template_ids", review["pond_id"].is_unique and set(review["pond_id"]) == candidate_ids,
                        candidate_count=len(candidate_ids)))
    checks.append(number_claim(text, "review_count", r"합한 (\d+)개", len(candidate_ids)))
    checks.append(check("review_pending", review["manual_review_status"].eq("PENDING_MANUAL_REVIEW").all(),
                        scope="Recorded review status; not proof of completed field review"))
    thresholds = evidence["thresholds_q25_q75"]
    checks.append(check("evidence_thresholds", thresholds["sgis_population_10min"]["q75"] == q_reach
                        and thresholds["sgis_population_gain_5_to_10"]["q75"] == q_gain))
    checks.append(check("source_years", raw["sgis_year"].eq(summary["year"]).all()
                        and population["year"].eq(2025).all()
                        and "2024" in pd.read_csv(ROOT / "data/manifests/sgis_sources.csv")["reference_period"].astype(str).tolist()))
    manifest = json_file("data/analysis/sgis_submission_figures_manifest.json")
    scatter = next(item for item in manifest["figures"] if item["file"].endswith("fig2_sgis_5_10_population.png"))
    checks.append(figure_cohort_check(scatter, paired))
    stale = []
    for figure in manifest["figures"]:
        for record in [figure, *figure["inputs"]]:
            relative = record.get("path", record.get("file"))
            path = ROOT / relative
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != record["sha256"]:
                stale.append(relative)
    checks.append(check("figure_input_and_output_hashes", not stale, stale_files=stale))
    validation = json_file("data/analysis/validation_report.json")
    for label, status in [("통과", "PASS"), ("경고", "WARN"), ("실패", "FAIL")]:
        checks.append(number_claim(text, f"validation_{status}", rf"(\d+)개 {label}",
                                   sum(row["status"] == status for row in validation["checks"])))
    return checks

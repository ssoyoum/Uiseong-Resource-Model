"""시나리오 기반 정책 검토 우선순위 점수(실험)와 가중치 민감도 분석.

가중치는 행정 기준이 아닌 정책 가정이다. 고정 점수를 제시하지 않고 4개 시나리오와
무작위 가중치 민감도로 상위 후보의 안정성을 함께 보고한다. 결측값은 대체하지 않고,
좌표 검토 대상과 SGIS 10분 인구 미확보 시설은 점수 산정에서 제외한다.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

try:
    from common import ANALYSIS_DIR, DATA_NOT_AVAILABLE, read_json, write_json
except ImportError:
    from analysis.common import ANALYSIS_DIR, DATA_NOT_AVAILABLE, read_json, write_json


RANDOM_SEED = 42
RANDOM_DRAWS = 1000
EXAMPLE_TOP_K = 20
MODEL_VERSION = "policy-priority-scenarios-0.1"

# (지표, 방향, 그룹) — 방향 +1은 값이 클수록 검토 우선, -1은 작을수록 우선
INDICATORS = [
    ("sgis_drive_population_10min", 1, "demand"),
    ("distance_to_road_m", -1, "access"),
    ("facility_count_1000m", 1, "amenity"),
    ("emd_youth_ratio", 1, "youth"),
    ("capacity", 1, "resource"),
    ("agricultural_ratio_1000m", 1, "resource"),
]
GROUP_DESCRIPTIONS = {
    "demand": "SGIS 생활권역 10분 주행 도달인구",
    "access": "VWorld UQ151 최근접 도로 유클리드거리(m)",
    "amenity": "VWorld UQ164·UO601 시설 1km 내 개수",
    "youth": "행정안전부 주민등록 읍·면 청년(19~39세) 비율",
    "resource": "못 저수용량과 1km 내 농업지역 비율",
}
GROUPS = list(GROUP_DESCRIPTIONS)
SCENARIOS = {
    "base": {group: 0.2 for group in GROUPS},
    # 접근성 강조는 도로접근(access)과 주변시설(amenity)을 함께 0.3씩 높인다.
    "access_emphasis": {group: 0.3 if group in ("access", "amenity") else 0.4 / 3 for group in GROUPS},
    "preservation_emphasis": {group: 0.4 if group == "resource" else 0.15 for group in GROUPS},
    "youth_activity_emphasis": {group: 0.4 if group == "youth" else 0.15 for group in GROUPS},
}


def load_frame() -> pd.DataFrame:
    payload = read_json(ANALYSIS_DIR / "pond_classification.json", {}) or {}
    frame = pd.DataFrame(payload.get("data") or [])
    frame["pond_id"] = frame["pond_id"].astype(str)
    review = pd.read_csv(ANALYSIS_DIR / "coordinate_correction_template.csv", dtype=str, keep_default_na=False)
    frame["coordinate_review_target"] = frame["pond_id"].isin(set(review["pond_id"]))
    return frame


def normalize(series: pd.Series, direction: int, method: str) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce") * direction
    if method == "percentile":
        return values.rank(pct=True, method="average")
    low, high = values.min(), values.max()
    return (values - low) / (high - low) if high > low else values * 0 + 0.5


def group_scores(frame: pd.DataFrame, method: str) -> pd.DataFrame:
    parts = {}
    for column, direction, group in INDICATORS:
        parts.setdefault(group, []).append(normalize(frame[column], direction, method))
    return pd.DataFrame({group: pd.concat(columns, axis=1).mean(axis=1) for group, columns in parts.items()}, index=frame.index)


def score(groups: pd.DataFrame, weights: dict[str, float]) -> pd.Series:
    return sum(groups[group] * weight for group, weight in weights.items()) * 100


def top_ids(scores: pd.Series, ids: pd.Series, k: int) -> set[str]:
    return set(ids.loc[scores.sort_values(ascending=False).index[:k]])


def run() -> dict:
    frame = load_frame()
    indicator_columns = [column for column, _, _ in INDICATORS]
    available = frame["sgis_drive_population_10min_status"] == "AVAILABLE"
    complete = frame[indicator_columns].apply(pd.to_numeric, errors="coerce").notna().all(axis=1)
    eligible_mask = available & complete & ~frame["coordinate_review_target"]
    exclusion = np.select(
        [frame["coordinate_review_target"], ~available, ~complete],
        ["COORDINATE_REVIEW_TARGET", "SGIS_10MIN_NOT_AVAILABLE", "INDICATOR_MISSING"],
        default="",
    )
    eligible = frame.loc[eligible_mask].reset_index(drop=True)
    if eligible.empty:
        result = {"status": DATA_NOT_AVAILABLE, "message": "점수 산정 가능한 시설 없음"}
        write_json(ANALYSIS_DIR / "policy_priority_scenarios.json", result)
        return result

    groups = group_scores(eligible, "percentile")
    groups_minmax = group_scores(eligible, "minmax")
    output = eligible[["pond_id", "emd_name", "classification_type"]].copy()
    for name, weights in SCENARIOS.items():
        output[f"score_{name}"] = score(groups, weights).round(2)
        output[f"rank_{name}"] = output[f"score_{name}"].rank(ascending=False, method="min").astype(int)
    output["score_base_minmax"] = score(groups_minmax, SCENARIOS["base"]).round(2)
    for group in GROUPS:
        output[f"group_{group}_percentile"] = groups[group].round(4)

    rng = np.random.default_rng(RANDOM_SEED)
    draws = rng.dirichlet(np.ones(len(GROUPS)), size=RANDOM_DRAWS)
    group_matrix = groups[GROUPS].to_numpy()
    top_counts = np.zeros(len(eligible), dtype=int)
    for weights in draws:
        random_scores = group_matrix @ weights
        top_counts[np.argsort(-random_scores)[:EXAMPLE_TOP_K]] += 1
    output["random_weight_top_k_frequency"] = (top_counts / RANDOM_DRAWS).round(3)
    output["policy_candidate_example_base"] = output["rank_base"] <= EXAMPLE_TOP_K
    output["status"] = "EXPERIMENTAL_POLICY_ASSUMPTION"

    excluded = frame.loc[~eligible_mask, ["pond_id"]].assign(exclusion_reason=exclusion[~eligible_mask.to_numpy()])
    output.to_csv(ANALYSIS_DIR / "policy_priority_scenarios.csv", index=False, encoding="utf-8-sig")
    excluded.to_csv(ANALYSIS_DIR / "policy_priority_excluded.csv", index=False, encoding="utf-8-sig")

    score_columns = {name: output[f"score_{name}"] for name in SCENARIOS}
    ids = output["pond_id"]
    base_top = top_ids(score_columns["base"], ids, EXAMPLE_TOP_K)
    summary = {
        "status": "EXPERIMENTAL_POLICY_ASSUMPTION",
        "model_version": MODEL_VERSION,
        "random_seed": RANDOM_SEED,
        "eligible_count": int(len(output)),
        "excluded_count": int(len(excluded)),
        "excluded_by_reason": excluded["exclusion_reason"].value_counts().to_dict(),
        "indicators": [
            {"column": column, "direction": "higher_is_priority" if direction > 0 else "lower_is_priority", "group": group}
            for column, direction, group in INDICATORS
        ],
        "groups": GROUP_DESCRIPTIONS,
        "normalization": "적격 시설 내 백분위 순위(동순위 평균); 그룹 내 복수 지표는 단순평균. Min-Max는 비교용(score_base_minmax)",
        "missing_rule": "결측 지표가 있는 시설은 대체하지 않고 점수 산정에서 제외",
        "weights": {name: {group: round(weight, 4) for group, weight in weights.items()} for name, weights in SCENARIOS.items()},
        "weight_rationale": "행정 기준 가중치가 없어 기본은 균등가중; 나머지는 강조 그룹 0.4 이상을 주는 정책 가정 시나리오",
        "sensitivity": {
            "spearman_vs_base": {
                name: round(float(score_columns["base"].corr(series, method="spearman")), 4)
                for name, series in score_columns.items() if name != "base"
            },
            "spearman_base_percentile_vs_minmax": round(float(output["score_base"].corr(output["score_base_minmax"], method="spearman")), 4),
            f"top{EXAMPLE_TOP_K}_overlap_with_base": {
                name: len(base_top & top_ids(series, ids, EXAMPLE_TOP_K))
                for name, series in score_columns.items() if name != "base"
            },
            f"top{EXAMPLE_TOP_K}_overlap_minmax_vs_base": len(base_top & top_ids(output["score_base_minmax"], ids, EXAMPLE_TOP_K)),
            "random_weight_draws": RANDOM_DRAWS,
            "random_weight_distribution": "Dirichlet(1,1,1,1,1)",
            "stable_candidates_frequency_ge_0_8": output.loc[output["random_weight_top_k_frequency"] >= 0.8, "pond_id"].tolist(),
            "base_top_k_with_frequency_lt_0_5": output.loc[output["policy_candidate_example_base"] & (output["random_weight_top_k_frequency"] < 0.5), "pond_id"].tolist(),
        },
        "outputs": ["data/analysis/policy_priority_scenarios.csv", "data/analysis/policy_priority_excluded.csv"],
        "use_policy": f"상위 {EXAMPLE_TOP_K}개는 '정책 우선후보 예시'이며 행정적으로 확정된 순위가 아니다. 현장 관리상태·보존가치·주민 수요는 반영되지 않았다.",
    }
    write_json(ANALYSIS_DIR / "policy_priority_scenarios.json", summary)
    return summary


if __name__ == "__main__":
    result = run()
    print(f"정책 우선순위 시나리오: {result['status']} (적격 {result.get('eligible_count')}개)")

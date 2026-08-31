"""Analyze SGIS route-catchment population results for decision support."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

try:
    from common import ANALYSIS_CRS, apply_coordinate_corrections, load_ponds
except ImportError:
    from analysis.common import ANALYSIS_CRS, apply_coordinate_corrections, load_ponds


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DIR = ROOT / "data" / "analysis"
SGIS_PATH = ROOT / "data" / "processed" / "population" / "sgis_drive_population.csv"
POND_SOURCE_PATH = ROOT / "data" / "processed" / "ponds.csv"
CONTEXT_PATH = ANALYSIS_DIR / "pond_context.csv"
CLASSIFICATION_PATH = ANALYSIS_DIR / "competition" / "pond_classification.json"
OUTPUT_CSV = ANALYSIS_DIR / "sgis_catchment_analysis.csv"
COORDINATE_AUDIT_CSV = ANALYSIS_DIR / "coordinate_quality_audit.csv"
OUTPUT_JSON = ANALYSIS_DIR / "sgis_catchment_analysis.json"
REPORT_PATH = ROOT / "docs" / "sgis-catchment-analysis.md"
FIGURES_DIR = ROOT / "analysis" / "figures"


def load_classification() -> pd.DataFrame:
    if not CLASSIFICATION_PATH.exists():
        return pd.DataFrame()
    payload = json.loads(CLASSIFICATION_PATH.read_text(encoding="utf-8"))
    frame = pd.DataFrame(payload.get("data", []))
    columns = ["pond_id", "classification_type", "classification_label", "accessibility_class"]
    return frame[[column for column in columns if column in frame.columns]].copy()


def load_data() -> pd.DataFrame:
    context = pd.read_csv(CONTEXT_PATH, dtype={"pond_id": str})
    ponds = apply_coordinate_corrections(load_ponds(ANALYSIS_CRS))[[
        "id", "geometry", "coordinate_correction_applied"
    ]].copy()
    ponds["pond_id"] = ponds["id"].astype(str)
    centroids = ponds.geometry.centroid
    ponds["coordinate_group_id"] = centroids.map(lambda point: f"{round(point.x):.0f}_{round(point.y):.0f}")
    coordinate_sizes = ponds["coordinate_group_id"].value_counts()
    ponds["coordinate_group_size"] = ponds["coordinate_group_id"].map(coordinate_sizes).astype(int)
    ponds["coordinate_quality"] = np.where(
        ponds["coordinate_group_size"].eq(1), "UNIQUE", "DUPLICATED_COORDINATE"
    )
    ponds["coordinate_source"] = "UNKNOWN"
    if POND_SOURCE_PATH.exists():
        source = pd.read_csv(POND_SOURCE_PATH, encoding="utf-8-sig", dtype=str)
        if {"연번", "CLSS"}.issubset(source.columns):
            source = source[["연번", "CLSS"]].rename(
                columns={"연번": "pond_id", "CLSS": "coordinate_source"}
            )
            source["pond_id"] = source["pond_id"].astype(str)
            ponds = ponds.drop(columns=["coordinate_source"]).merge(
                source, on="pond_id", how="left", validate="one_to_one"
            )
            ponds["coordinate_source"] = ponds["coordinate_source"].fillna("UNKNOWN")
    ponds["coordinate_validation"] = np.select(
        [
            ponds["coordinate_correction_applied"],
            ponds["coordinate_source"].eq("시군구 좌표"),
            ponds["coordinate_source"].eq("인근좌표"),
            ponds["coordinate_quality"].eq("DUPLICATED_COORDINATE"),
        ],
        [
            "CORRECTED_POINT",
            "UNVERIFIED_ADMIN_POINT",
            "UNVERIFIED_NEARBY_POINT",
            "DUPLICATED_COORDINATE",
        ],
        default="RELIABLE_POINT",
    )
    ponds["sgis_analysis_eligible"] = ponds["coordinate_validation"].isin(
        ["RELIABLE_POINT", "CORRECTED_POINT"]
    )
    ponds = ponds.drop(columns=["id", "geometry"])
    sgis = pd.read_csv(SGIS_PATH, dtype={"pond_id": str})
    key = ["pond_id", "sgis_year", "drive_time_min"]
    sgis = sgis.drop_duplicates(key, keep="last")
    sgis["drive_time_min"] = pd.to_numeric(sgis["drive_time_min"], errors="coerce")
    sgis["sgis_population"] = pd.to_numeric(sgis["sgis_population"], errors="coerce")
    sgis["service_area_m2"] = pd.to_numeric(sgis["service_area_m2"], errors="coerce")

    values = sgis.pivot(index="pond_id", columns="drive_time_min", values="sgis_population")
    values = values.rename(columns={5: "sgis_population_5min", 10: "sgis_population_10min"})
    areas = sgis.pivot(index="pond_id", columns="drive_time_min", values="service_area_m2")
    areas = areas.rename(columns={5: "sgis_area_5min_m2", 10: "sgis_area_10min_m2"})
    statuses = sgis.pivot(index="pond_id", columns="drive_time_min", values="status")
    statuses = statuses.rename(columns={5: "sgis_status_5min", 10: "sgis_status_10min"})

    result = context.merge(values.reset_index(), on="pond_id", how="left")
    result = result.merge(ponds, on="pond_id", how="left", validate="one_to_one")
    result = result.merge(areas.reset_index(), on="pond_id", how="left")
    result = result.merge(statuses.reset_index(), on="pond_id", how="left")
    classification = load_classification()
    if not classification.empty:
        result = result.merge(classification, on="pond_id", how="left")

    result["sgis_has_5min"] = result["sgis_population_5min"].notna()
    result["sgis_has_10min"] = result["sgis_population_10min"].notna()
    result["sgis_has_both"] = result["sgis_has_5min"] & result["sgis_has_10min"]
    result["sgis_coverage_class"] = np.select(
        [
            result["sgis_has_both"],
            result["sgis_has_5min"],
            result["sgis_has_10min"],
        ],
        ["BOTH", "5MIN_ONLY", "10MIN_ONLY"],
        default="NONE",
    )
    result["sgis_population_gain_5_to_10"] = np.where(
        result["sgis_has_both"],
        result["sgis_population_10min"] - result["sgis_population_5min"],
        np.nan,
    )
    result["sgis_population_ratio_10_to_5"] = np.where(
        result["sgis_has_both"] & (result["sgis_population_5min"] > 0),
        result["sgis_population_10min"] / result["sgis_population_5min"],
        np.nan,
    )
    result["sgis_population_density_10min_per_km2"] = np.where(
        result["sgis_has_10min"] & (result["sgis_area_10min_m2"] > 0),
        result["sgis_population_10min"] / (result["sgis_area_10min_m2"] / 1_000_000),
        np.nan,
    )
    for column in (
        "sgis_population_5min",
        "sgis_population_10min",
        "sgis_population_gain_5_to_10",
        "sgis_population_density_10min_per_km2",
    ):
        result[f"{column}_rank_pct"] = result[column].rank(pct=True)
    return result


def numeric_summary(frame: pd.DataFrame, column: str) -> dict[str, float | int | None]:
    values = pd.to_numeric(frame[column], errors="coerce").dropna()
    if values.empty:
        return {"count": 0, "min": None, "max": None, "mean": None, "median": None}
    return {
        "count": int(values.size),
        "min": float(values.min()),
        "max": float(values.max()),
        "mean": float(values.mean()),
        "median": float(values.median()),
    }


def correlation(frame: pd.DataFrame, x: str, y: str) -> dict[str, float | int | None]:
    pair = frame[[x, y]].apply(pd.to_numeric, errors="coerce").dropna()
    if len(pair) < 3:
        return {"n": int(len(pair)), "spearman_r": None, "p_value": None}
    statistic, p_value = spearmanr(pair[x], pair[y])
    return {"n": int(len(pair)), "spearman_r": float(statistic), "p_value": float(p_value)}


def make_figures(frame: pd.DataFrame) -> list[str]:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    outputs: list[str] = []
    point_frame = frame[frame["sgis_analysis_eligible"]].drop_duplicates(
        "coordinate_group_id", keep="first"
    )
    available = point_frame[point_frame["sgis_has_10min"]].copy().sort_values("sgis_population_10min", ascending=False).head(20)
    if not available.empty:
        plot = available.sort_values("sgis_population_10min")
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.barh(plot["pond_id"].astype(str), plot["sgis_population_10min"], color="#2563eb")
        ax.set_title("Top 20 facilities by SGIS 10-minute driving population")
        ax.set_xlabel("Population (privacy-protected SGIS service value)")
        ax.set_ylabel("Pond ID")
        fig.tight_layout()
        path = FIGURES_DIR / "10_sgis_top_10min_population.png"
        fig.savefig(path, dpi=180)
        plt.close(fig)
        outputs.append(str(path.relative_to(ROOT)).replace("\\", "/"))

    paired = point_frame[point_frame["sgis_has_both"]]
    if not paired.empty:
        fig, ax = plt.subplots(figsize=(8, 7))
        ax.scatter(paired["sgis_population_5min"], paired["sgis_population_10min"], alpha=0.65, color="#0f766e")
        maximum = max(paired["sgis_population_5min"].max(), paired["sgis_population_10min"].max())
        ax.plot([0, maximum], [0, maximum], linestyle="--", color="#6b7280", linewidth=1)
        ax.set_title("SGIS 5-minute vs 10-minute driving population")
        ax.set_xlabel("5-minute population")
        ax.set_ylabel("10-minute population")
        fig.tight_layout()
        path = FIGURES_DIR / "11_sgis_5_vs_10_population.png"
        fig.savefig(path, dpi=180)
        plt.close(fig)
        outputs.append(str(path.relative_to(ROOT)).replace("\\", "/"))

    regional = (
        point_frame.groupby("emd_name", dropna=False)
        .agg(mean_10min=("sgis_population_10min", "mean"), available_10min=("sgis_has_10min", "sum"))
        .sort_values("mean_10min")
        .tail(18)
    )
    if not regional.empty:
        labels = [str(value) for value in regional.index]
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.barh(labels, regional["mean_10min"], color="#ea580c")
        ax.set_title("Mean SGIS 10-minute driving population by EMD")
        ax.set_xlabel("Mean population")
        ax.set_ylabel("EMD")
        fig.tight_layout()
        path = FIGURES_DIR / "12_sgis_emd_mean_population.png"
        fig.savefig(path, dpi=180)
        plt.close(fig)
        outputs.append(str(path.relative_to(ROOT)).replace("\\", "/"))
    return outputs


def markdown_report(summary: dict, top_reach: pd.DataFrame, top_gain: pd.DataFrame) -> str:
    def table(frame: pd.DataFrame, value_column: str) -> str:
        columns = ["pond_id", "emd_name", "capacity", value_column, "classification_label"]
        columns = [column for column in columns if column in frame.columns]
        view = frame[columns].head(10).copy()
        if value_column in view.columns:
            view[value_column] = view[value_column].round(1)
        return view.to_markdown(index=False) if not view.empty else "(자료 없음)"

    lines = [
        "# SGIS 생활권역 주행인구 분석",
        "",
        f"- 기준연도: `{summary['year']}`",
        f"- 분석 시설: `{summary['facility_count']}`개",
        f"- 고유 좌표: `{summary['coordinate_quality']['unique_coordinate_points']}`개",
        f"- 중복 좌표 연관 시설: `{summary['coordinate_quality']['facilities_in_duplicated_groups']}`개",
        f"- 실제 좌표 보정 완료 시설: `{summary['coordinate_quality']['corrected_facilities']}`개",
        f"- 인근좌표 시설: `{summary['coordinate_quality']['unverified_nearby_point_facilities']}`개",
        f"- 분석에 사용한 검증 좌표: `{summary['coordinate_quality']['reliable_unique_points']}`개",
        f"- 검증 좌표 기준 5분 인구 응답: `{summary['coverage']['available_5min']}`개",
        f"- 검증 좌표 기준 10분 인구 응답: `{summary['coverage']['available_10min']}`개",
        f"- 검증 좌표 기준 5분·10분 모두 응답: `{summary['coverage']['available_both']}`개",
        f"- 원자료 시설 기준 5분/10분 응답: `{summary['raw_facility_coverage']['available_5min']}`/`{summary['raw_facility_coverage']['available_10min']}`개",
        f"- 미응답 원인: 위치 인식 실패 `{summary['sgis_response_diagnostics']['unlocated_error_rows']}`행, 통계값 미반환 `{summary['sgis_response_diagnostics']['no_population_value_rows']}`행",
        "",
        "## 핵심 해석",
        "",
        "1. 5분·10분 생활권은 시설별로 겹치므로 인구를 시설 간 합산하지 않고 개별 시설의 도달 규모로 비교한다.",
        "2. SGIS 응답값은 비밀보호 처리된 서비스 제공값이며, `DATA_NOT_AVAILABLE`을 0명으로 해석하지 않는다.",
        "3. 10분 인구가 큰 시설은 광역 접근 수요 후보이고, 5→10분 증가폭이 큰 시설은 외곽 확장 효과 후보로 본다.",
        "4. 상관관계는 우선 탐색 결과이며 인과관계나 사업효과를 의미하지 않는다.",
        "5. 동일 좌표 또는 시군구 대표점으로 표시된 시설은 실제 개별 위치가 확인될 때까지 순위·상관·읍면 요약에서 제외했다.",
        "6. 제외된 SGIS 응답값은 원자료 대조를 위해 CSV에 보존했지만 시설별 고유 수요로 해석하지 않는다.",
        "",
        "## 10분 도달인구 상위 시설",
        "",
        table(top_reach, "sgis_population_10min"),
        "",
        "## 5분→10분 증가폭 상위 시설",
        "",
        table(top_gain, "sgis_population_gain_5_to_10"),
        "",
        "## 산출물",
        "",
        "- `data/analysis/sgis_catchment_analysis.csv`: 시설별 분석 테이블",
        "- `data/analysis/coordinate_quality_audit.csv`: 좌표 중복·대표점 제외 감사표",
        "- `data/analysis/sgis_catchment_analysis.json`: 요약·상관관계·읍면 집계",
        "- `analysis/figures/10_sgis_top_10min_population.png`",
        "- `analysis/figures/11_sgis_5_vs_10_population.png`",
        "- `analysis/figures/12_sgis_emd_mean_population.png`",
        "",
        "## 다음 판단",
        "",
        "- 상위 시설을 현장관리 상태·보존가치·도로 접근성과 교차검토한다.",
        "- SGIS 인구를 분류 점수에 바로 반영하지 않고, 가중치 민감도 분석 후 반영 여부를 결정한다.",
        "- 제출본에는 SGIS 기준연도, 비밀보호 처리, 미제공 건 처리방식을 명시한다.",
    ]
    return "\n".join(lines) + "\n"


def run() -> dict:
    frame = load_data()
    numeric_columns = [
        "sgis_population_5min",
        "sgis_population_10min",
        "sgis_population_gain_5_to_10",
        "sgis_population_ratio_10_to_5",
        "sgis_population_density_10min_per_km2",
    ]
    frame.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    audit_columns = [
        "pond_id", "address", "region", "emd_name", "capacity", "coordinate_source",
        "coordinate_correction_applied",
        "coordinate_group_id", "coordinate_group_size", "coordinate_quality",
        "coordinate_validation", "sgis_analysis_eligible",
    ]
    frame[[column for column in audit_columns if column in frame.columns]].to_csv(
        COORDINATE_AUDIT_CSV, index=False, encoding="utf-8-sig"
    )
    point_frame = frame[frame["sgis_analysis_eligible"]].drop_duplicates(
        "coordinate_group_id", keep="first"
    )
    available_10 = point_frame[point_frame["sgis_has_10min"]]
    available_both = point_frame[point_frame["sgis_has_both"]]
    raw_sgis = pd.read_csv(SGIS_PATH, dtype={"pond_id": str})
    unavailable = raw_sgis[raw_sgis["status"].eq("DATA_NOT_AVAILABLE")].copy()
    error_text = unavailable["error"].fillna("").astype(str)
    unlocated_rows = error_text.str.contains("unlocated|Invalid locations", case=False, regex=True)
    no_population_rows = unavailable["sgis_population"].isna() & unavailable["error"].isna()
    sgis_response_diagnostics = {
        "data_not_available_rows": int(len(unavailable)),
        "unlocated_error_rows": int(unlocated_rows.sum()),
        "unlocated_error_facilities": int(unavailable.loc[unlocated_rows, "pond_id"].nunique()),
        "no_population_value_rows": int(no_population_rows.sum()),
        "no_population_value_facilities": int(unavailable.loc[no_population_rows, "pond_id"].nunique()),
        "interpretation": (
            "unlocated rows are route-network input location failures; "
            "no-population rows received a service area but no population value"
        ),
    }
    raw_facility_coverage = {
        "available_5min": int(frame["sgis_has_5min"].sum()),
        "available_10min": int(frame["sgis_has_10min"].sum()),
        "available_both": int(frame["sgis_has_both"].sum()),
    }
    year_values = pd.read_csv(SGIS_PATH, usecols=["sgis_year"])["sgis_year"].dropna().unique().tolist()
    summary = {
        "status": "PASS",
        "year": int(year_values[0]) if len(year_values) == 1 else year_values,
        "facility_count": int(len(frame)),
        "coordinate_quality": {
            "unique_coordinate_points": int(frame["coordinate_group_id"].nunique()),
            "duplicated_coordinate_groups": int(
                frame.loc[frame["coordinate_group_size"] > 1, "coordinate_group_id"].nunique()
            ),
            "facilities_in_duplicated_groups": int(
                frame.loc[frame["coordinate_group_size"] > 1, "pond_id"].nunique()
            ),
            "corrected_facilities": int(frame["coordinate_correction_applied"].sum()),
            "unverified_admin_point_facilities": int(
                frame["coordinate_source"].eq("시군구 좌표").sum()
            ),
            "unverified_nearby_point_facilities": int(
                frame["coordinate_source"].eq("인근좌표").sum()
            ),
            "reliable_unique_points": int(point_frame["coordinate_group_id"].nunique()),
            "analysis_unit_for_rank_correlations_and_regional_summary": "unique_coordinate_point",
        },
        "coverage": {
            "available_5min": int(point_frame["sgis_has_5min"].sum()),
            "available_10min": int(point_frame["sgis_has_10min"].sum()),
            "available_both": int(point_frame["sgis_has_both"].sum()),
            "none": int((point_frame["sgis_coverage_class"] == "NONE").sum()),
        },
        "raw_facility_coverage": raw_facility_coverage,
        "sgis_response_diagnostics": sgis_response_diagnostics,
        "distributions": {column: numeric_summary(point_frame, column) for column in numeric_columns},
        "correlations_with_10min_population": {
            column: correlation(available_10, "sgis_population_10min", column)
            for column in ("capacity", "distance_to_road_m", "facility_count_1000m", "agricultural_ratio_1000m")
            if column in available_10.columns
        },
        "regional_summary": [],
        "method_notes": [
            "SGIS route-based service-area population, separate from official-grid Buffer population.",
            "Overlapping service areas mean facility populations are not additive.",
            "SGIS privacy-protected service values and missing responses are preserved as provided.",
            "Facilities with CLSS=시군구 좌표 or duplicated coordinates are excluded from inferential summaries until corrected.",
        ],
    }
    regional = (
        point_frame.groupby("emd_name", dropna=False)
        .agg(
            coordinate_point_count=("pond_id", "count"),
            available_5min=("sgis_has_5min", "sum"),
            available_10min=("sgis_has_10min", "sum"),
            mean_5min=("sgis_population_5min", "mean"),
            median_5min=("sgis_population_5min", "median"),
            mean_10min=("sgis_population_10min", "mean"),
            median_10min=("sgis_population_10min", "median"),
            mean_gain_5_to_10=("sgis_population_gain_5_to_10", "mean"),
        )
        .reset_index()
        .sort_values("mean_10min", ascending=False, na_position="last")
    )
    summary["regional_summary"] = regional.where(pd.notna(regional), None).to_dict(orient="records")
    OUTPUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    top_reach = available_10.sort_values("sgis_population_10min", ascending=False)
    top_gain = available_both.sort_values("sgis_population_gain_5_to_10", ascending=False)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(markdown_report(summary, top_reach, top_gain), encoding="utf-8")
    summary["figures"] = make_figures(frame)
    OUTPUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, ensure_ascii=False, indent=2))

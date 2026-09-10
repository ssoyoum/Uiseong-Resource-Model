"""Rebuild the three SGIS submission figures from checked local analysis outputs.

Run after the SGIS catchment and policy-evidence analyses. No values are imputed,
no coordinates are moved, and the plotting cohort is recorded in a manifest.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import ScalarFormatter
from matplotlib.lines import Line2D
import pandas as pd
import numpy as np

try:
    from common import ANALYSIS_CRS, apply_coordinate_corrections, load_ponds
except ImportError:
    from analysis.common import ANALYSIS_CRS, apply_coordinate_corrections, load_ponds


ROOT = Path(__file__).resolve().parents[1]
FIGURE_DIR = ROOT / "docs/submission/figures"
MANIFEST_PATH = ROOT / "data/analysis/sgis_submission_figures_manifest.json"
SCRIPT_PATH = "analysis/generate_sgis_submission_figures.py"
SGIS_PATH = "data/analysis/sgis_catchment_analysis.csv"
SUMMARY_PATH = "data/analysis/sgis_catchment_analysis.json"
POLICY_PATH = "data/analysis/sgis_policy_evidence.csv"
CLASSIFICATION_PATH = "data/analysis/pond_classification.csv"
BOUNDARY_PATH = "data/geojson/uiseong_boundary.geojson"
GREEN = "#28745f"
INK = "#223a35"
RUST = "#b35f40"

POLICY_LABELS = {
    "ACCESS_AND_REACH_REVIEW": "접근·도달 검토",
    "YOUTH_PARTICIPATION_REVIEW": "청년참여 검토",
    "COMMUNITY_SUPPORT_REVIEW": "공동체 지원 검토",
    "FIELD_REVIEW_REQUIRED": "현장 확인 필요",
    "INSUFFICIENT_SGIS_10MIN": "SGIS 10분 인구 미확보",
    "CONTEXT_ONLY": "맥락 참고",
}
TYPE_LABELS = {
    "D_PRESERVATION": "보존·기록형",
    "A_CULTURE_TOURISM": "문화·관광형",
    "B_ECO_EDUCATION": "생태·교육형",
    "C_COMMUNITY": "공동체형",
    "E_MANAGEMENT_PRIORITY": "관리우선형",
}


def read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def boolean(series: pd.Series) -> pd.Series:
    values = series.astype(str).str.lower()
    if not values.isin(["true", "false"]).all():
        raise ValueError(f"Invalid boolean values in {series.name}")
    return values.eq("true")


def input_metadata(paths: list[str]) -> list[dict]:
    return [
        {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}
        for path in paths
    ]


def save_figure(fig: plt.Figure, name: str, caption: str, paths: list[str], **details) -> dict:
    path = FIGURE_DIR / name
    fig.savefig(path, dpi=180, facecolor="white", metadata={"Description": caption, "Software": SCRIPT_PATH})
    plt.close(fig)
    return {
        "file": path.relative_to(ROOT).as_posix(),
        "generator": SCRIPT_PATH,
        "inputs": input_metadata(paths),
        "caption": caption,
        "font_family": "Noto Sans KR",
        "creator": "작성자 분석·시각화",
        "status": "AVAILABLE",
        "size_bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        **details,
    }


def distribution_figure(frame: pd.DataFrame) -> dict:
    ponds = apply_coordinate_corrections(load_ponds(ANALYSIS_CRS))
    ponds = ponds.merge(
        frame[["pond_id", "sgis_analysis_eligible", "coordinate_group_id"]],
        left_on="id", right_on="pond_id", validate="one_to_one",
    )
    if len(ponds) != len(frame):
        raise ValueError("Map and SGIS cohorts have different pond IDs")
    actual_groups = ponds.geometry.map(lambda point: f"{round(point.x):.0f}_{round(point.y):.0f}")
    if not actual_groups.eq(ponds["coordinate_group_id"]).all():
        raise ValueError("Coordinates changed after SGIS analysis; rerun the SGIS analysis first")
    boundary = gpd.read_file(ROOT / BOUNDARY_PATH).to_crs(ANALYSIS_CRS)
    eligible = ponds[ponds["sgis_analysis_eligible"]]
    excluded = ponds[~ponds["sgis_analysis_eligible"]]
    unique_points = int(ponds["coordinate_group_id"].nunique())
    fig, ax = plt.subplots(figsize=(10, 8))
    fig.subplots_adjust(left=0.045, right=0.965, bottom=0.18, top=0.86)
    boundary.plot(ax=ax, color="#f3f0e8", edgecolor="#64736b", linewidth=1.15)
    eligible.plot(ax=ax, color=GREEN, edgecolor="white", linewidth=0.35, markersize=18, alpha=0.8)
    excluded.drop_duplicates("coordinate_group_id").plot(
        ax=ax, color=RUST, marker="x", markersize=70, linewidth=1.7,
    )
    ax.set_axis_off()
    fig.suptitle(f"의성군 전통 못 {len(ponds)}개: 위치와 좌표 품질", fontsize=23, weight="bold", y=0.965)
    fig.text(0.5, 0.91, f"고유 좌표 {unique_points}곳 · 좌표 보정 전 현황", ha="center", fontsize=14, color="#5d6b65")
    handles = [
        Line2D([], [], marker="o", color="none", markerfacecolor=GREEN, markeredgecolor="white", markersize=9,
               label=f"좌표 품질 조건 통과 {len(eligible)}개"),
        Line2D([], [], marker="x", color=RUST, linestyle="none", markersize=9,
               label=f"대표·인근·중복좌표 {len(excluded)}개"),
    ]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.125), ncol=2, frameon=False, fontsize=13)
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    sx, sy = xmin + (xmax - xmin) * 0.06, ymin + (ymax - ymin) * 0.09
    ax.plot([sx, sx + 10000], [sy, sy], color=INK, linewidth=2)
    ax.text(sx + 5000, sy + 700, "10 km", ha="center", fontsize=11, color=INK)
    ax.annotate("N", xy=(0.94, 0.9), xytext=(0.94, 0.76), xycoords="axes fraction",
                ha="center", fontsize=14, color=INK, arrowprops={"arrowstyle": "-|>", "color": INK})
    fig.text(0.04, 0.085, "출처: 본 연구 보유 못 좌표·경계 및 좌표 품질 분석 [출처 6] | 작성자 시각화 | EPSG:5174", fontsize=11, color="#58635e")
    fig.text(0.04, 0.045, "동일 좌표는 겹쳐 표시함. 품질 조건 통과는 현장에서 실제 위치를 확인했다는 뜻이 아님.", fontsize=11, color="#58635e")
    caption = (f"그림 1. 의성군 전통 못 {len(ponds)}개 ID의 입력좌표 분포. 고유 좌표 {unique_points}곳, "
               f"좌표 품질 조건 통과 {len(eligible)}개, 대표·인근·중복좌표 {len(excluded)}개. "
               "중첩 좌표를 임의로 분산하지 않았으며 실제 위치 전수검증 결과가 아니다. EPSG:5174.")
    paths = ["data/geojson/ponds.geojson", BOUNDARY_PATH, SGIS_PATH]
    correction_path = "data/analysis/coordinate_correction_template.csv"
    if (ROOT / correction_path).exists():
        paths.append(correction_path)
    return save_figure(
        fig, "fig1_pond_distribution_427.png", caption, paths,
        crs=ANALYSIS_CRS, facility_count=len(ponds), unique_coordinate_points=unique_points,
        eligible_facility_count=len(eligible), excluded_coordinate_quality=len(excluded),
        method="Original coordinates with recorded corrections only; no jitter; quality cohorts shown separately",
    )


def catchment_figure(frame: pd.DataFrame, summary: dict) -> dict:
    points = frame[frame["sgis_analysis_eligible"]].drop_duplicates("coordinate_group_id")
    paired = points[
        points["sgis_has_both"]
        & points["sgis_population_5min"].notna()
        & points["sgis_population_10min"].notna()
    ].copy()
    if len(paired) != summary["coverage"]["available_both"]:
        raise ValueError("Figure cohort differs from SGIS summary")
    if paired.empty:
        raise ValueError("DATA_NOT_AVAILABLE: no eligible paired SGIS population values")
    x = paired["sgis_population_5min"]
    y = paired["sgis_population_10min"]
    for column in ["sgis_population_5min", "sgis_population_10min"]:
        if paired[column].max() > summary["distributions"][column]["max"]:
            raise ValueError("Figure contains a value outside the eligible SGIS distribution")
    fig, ax = plt.subplots(figsize=(10, 7))
    fig.subplots_adjust(left=0.105, right=0.965, bottom=0.19, top=0.82)
    ax.scatter(x, y, s=39, alpha=0.7, color=GREEN, edgecolors="white", linewidths=0.4, zorder=3)
    xmax, ymax = float(x.max()) * 1.1, float(y.max()) * 1.08
    diagonal = np.geomspace(max(1, float(x.min()) * 0.75), min(xmax, ymax), 200)
    ax.plot(diagonal, diagonal, linestyle="--", color="#9caaa2", linewidth=1.3,
            label="5분 인구 = 10분 인구")
    ax.set_xscale("log")
    ax.set_xlim(max(1, float(x.min()) * 0.75), xmax)
    ax.set_xticks([5, 10, 20, 50, 100, 200, 500, 1000, 2000])
    ax.xaxis.set_major_formatter(ScalarFormatter())
    ax.set_ylim(-ymax * 0.025, ymax)
    ax.set_xlabel("5분 주행생활권 인구 (명, 로그축)", fontsize=15, labelpad=10)
    top = paired.loc[x.idxmax()]
    ax.annotate(f"ID {top['pond_id']} · {int(top['sgis_population_5min']):,} → {int(top['sgis_population_10min']):,}명",
                xy=(top['sgis_population_5min'], top['sgis_population_10min']),
                xytext=(-16, -35), textcoords="offset points", ha="right", fontsize=11,
                arrowprops={"arrowstyle": "->", "color": RUST}, color=RUST)
    ax.set_ylabel("10분 주행생활권 인구 (명)", fontsize=15, labelpad=10)
    ax.grid(color="#e4e8e5", linewidth=0.7)
    ax.set_axisbelow(True)
    ax.legend(loc="lower right", frameon=False, fontsize=11)
    fig.suptitle("SGIS 5분·10분 주행생활권 인구 비교", fontsize=23, weight="bold", y=0.965)
    fig.text(0.5, 0.89, f"{summary['year']}년 인구 · 좌표 품질 조건 통과 및 두 시간대 모두 응답한 {len(paired)}개 못",
             ha="center", fontsize=13, color="#5d6b65")
    fig.text(0.04, 0.082, "출처: SGIS, 2024년 기준 생활권역 통계 응답 [출처 1] · 작성자 분석·시각화", fontsize=11, color="#58635e")
    fig.text(0.04, 0.042, "미확보값은 0명으로 대체하지 않음. 못 간 생활권 인구는 합산하지 않으며 실제 방문수요를 뜻하지 않음.",
             fontsize=11, color="#58635e")
    caption = (f"그림 2. {summary['year']}년 SGIS 5분·10분 주행생활권 인구. 좌표 품질 조건을 통과한 고유 좌표 중 "
               f"두 시간대 모두 응답한 {len(paired)}개를 비교했다. "
               f"5분 최댓값 {x.max():,.0f}명, 10분 최댓값 {y.max():,.0f}명. X축은 로그축이며 큰 값을 삭제하지 않았다. 시설 간 인구 합산 및 결측값 대체는 하지 않았다.")
    return save_figure(
        fig, "fig2_sgis_5_10_population.png", caption, [SGIS_PATH, SUMMARY_PATH],
        reference_year=summary["year"], paired_count=len(paired),
        eligible_facility_count=len(points), population_5min_max=float(x.max()), population_10min_max=float(y.max()),
        plotted_pond_ids=paired["pond_id"].tolist(),
        x_scale="log", y_scale="linear", font_family="Noto Sans KR", excluded_due_to_magnitude=0,
        method="sgis_analysis_eligible == True; unique coordinate_group_id; both population values available",
    )


def classification_figure(frame: pd.DataFrame) -> dict:
    policy = pd.read_csv(ROOT / POLICY_PATH, dtype={"pond_id": str})
    types = pd.read_csv(ROOT / CLASSIFICATION_PATH, dtype={"pond_id": str})
    expected_ids = set(frame["pond_id"])
    for source in [policy, types]:
        if source["pond_id"].duplicated().any() or set(source["pond_id"]) != expected_ids:
            raise ValueError("Classification must contain exactly one row per analysis pond ID")
    policy_counts = policy["policy_review_context"].value_counts()
    type_counts = types["classification_type"].value_counts()
    if set(policy_counts.index) - set(POLICY_LABELS) or set(type_counts.index) - set(TYPE_LABELS):
        raise ValueError("Unrecognized policy context or classification type")
    context_order = list(POLICY_LABELS)
    type_order = [name for name in TYPE_LABELS if type_counts.get(name, 0) > 0]
    fig, axes = plt.subplots(1, 2, figsize=(13, 6), gridspec_kw={"width_ratios": [1.22, 1]})
    fig.subplots_adjust(left=0.19, right=0.96, bottom=0.22, top=0.73, wspace=0.6)
    colors = [GREEN, "#c38a2c", "#7185a0", RUST, "#b6b0a4", "#8ca38b"]
    for ax, order, counts, labels, palette, title in [
        (axes[0], context_order, policy_counts, POLICY_LABELS, colors, "정책 검토 맥락"),
        (axes[1], type_order, type_counts, TYPE_LABELS, ["#67765f", "#b7853c", "#3d8479", "#7185a0", RUST], "규칙기반 활용유형"),
    ]:
        values = [int(counts.get(name, 0)) for name in order]
        bars = ax.barh([labels[name] for name in order], values, color=palette[:len(order)], height=0.64)
        ax.invert_yaxis()
        ax.set_xlim(0, max(values) * 1.24)
        ax.bar_label(bars, labels=[f"{value}개" for value in values], padding=6, fontsize=13)
        ax.set_title(title, fontsize=18, weight="bold", pad=16)
        ax.set_xlabel("못 수 (개)", fontsize=12)
        ax.tick_params(axis="y", length=0, labelsize=12)
        ax.grid(axis="x", color="#e4e8e5", linewidth=0.7)
        ax.set_axisbelow(True)
        for spine in ax.spines.values():
            spine.set_visible(False)
    fig.suptitle(f"{len(frame)}개 못의 정책 검토 맥락과 활용유형", fontsize=24, weight="bold", y=0.96)
    fig.text(0.5, 0.866, f"서로 목적이 다른 두 분류체계 · 각 체계에서 {len(frame)}개 ID에 하나의 라벨 부여",
             ha="center", fontsize=14, color="#5d6b65")
    fig.text(0.035, 0.115, "출처: SGIS·행정안전부·본 연구 분석 [출처 1·2·6] | 작성자 시각화 | SGIS 미확보는 좌표 조건 통과 시설 내 집계",
             fontsize=11, color="#58635e")
    fig.text(0.035, 0.067, "보존·기록형은 보수적 기본 분류이며 보존가치 확정이 아님. 활용유형에는 SGIS 인구를 판정조건으로 사용하지 않음.",
             fontsize=11, color="#58635e")
    caption = (f"그림 3. {len(frame)}개 못의 정책 검토 맥락과 별도 규칙기반 활용유형. "
               f"각 체계의 라벨은 상호배타적이며 합계는 각각 {len(frame)}개다. 보존·기록형은 활용조건 미충족 시 기본 분류로, "
               "보존가치·정책 우선순위 확정 결과가 아니다.")
    return save_figure(
        fig, "fig3_policy_context_and_classification.png", caption, [POLICY_PATH, CLASSIFICATION_PATH, SGIS_PATH],
        facility_count=len(frame),
        policy_context_counts={key: int(policy_counts.get(key, 0)) for key in context_order},
        classification_counts={key: int(type_counts[key]) for key in type_order},
        method="Separate value_counts of exclusive policy_review_context and classification_type; no combined score",
    )


def run() -> dict:
    for font in ["NotoSansKR-Regular.ttf", "NotoSansKR-Bold.ttf"]:
        path = Path("C:/Windows/Fonts") / font
        if path.exists():
            font_manager.fontManager.addfont(str(path))
    font_manager.findfont("Noto Sans KR", fallback_to_default=False)
    plt.rcParams.update({
        "font.family": ["Noto Sans KR"],
        "axes.unicode_minus": False,
        "font.size": 12,
        "text.color": INK,
        "axes.labelcolor": INK,
        "xtick.color": "#55655e",
        "ytick.color": INK,
    })
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(ROOT / SGIS_PATH, dtype={"pond_id": str})
    summary = read_json(SUMMARY_PATH)
    if frame["pond_id"].duplicated().any() or len(frame) != summary["facility_count"]:
        raise ValueError("SGIS cohort has duplicate or missing pond IDs")
    for name in ["sgis_analysis_eligible", "sgis_has_both"]:
        frame[name] = boolean(frame[name])
    figures = [distribution_figure(frame), catchment_figure(frame, summary), classification_figure(frame)]
    manifest = {
        "status": "AVAILABLE_WITH_DOCUMENTED_LIMITATIONS",
        "generator": SCRIPT_PATH,
        "run_command": f"python {SCRIPT_PATH}",
        "facility_count": len(frame),
        "note": "Rebuild after upstream SGIS and classification outputs; field accuracy and policy effectiveness are not validated by these figures.",
        "figures": figures,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    output = run()
    print(f"SGIS submission figures: {len(output['figures'])} generated; paired cohort={output['figures'][1]['paired_count']}")

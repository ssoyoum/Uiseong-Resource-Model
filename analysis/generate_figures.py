"""공모전용 그림 10종을 자동 생성한다.

실제 입력이 없는 그림은 빈 수치를 채우지 않고 DATA_NOT_AVAILABLE 라벨을 그린다.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

try:
    from common import ANALYSIS_DIR, DATA_NOT_AVAILABLE, FIGURES_DIR, ensure_output_dirs, read_json, write_json
except ImportError:
    from analysis.common import ANALYSIS_DIR, DATA_NOT_AVAILABLE, FIGURES_DIR, ensure_output_dirs, read_json, write_json


plt.rcParams["font.family"] = ["Malgun Gothic", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def unavailable(path: Path, title: str, message: str = DATA_NOT_AVAILABLE) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.axis("off")
    ax.text(0.5, 0.58, title, ha="center", va="center", fontsize=16, weight="bold")
    ax.text(0.5, 0.42, message, ha="center", va="center", fontsize=13, color="#b06b00")
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def run() -> dict:
    ensure_output_dirs()
    status = {}
    pond_path = Path("data/processed/ponds.csv")
    ponds = pd.read_csv(pond_path) if pond_path.exists() else pd.DataFrame()
    capacity = pd.to_numeric(ponds.iloc[:, 2], errors="coerce") if not ponds.empty else pd.Series(dtype=float)

    unavailable(FIGURES_DIR / "01_population_trend.png", "읍·면별 인구 추이")
    unavailable(FIGURES_DIR / "02_youth_elderly.png", "청년·고령인구 비율")
    unavailable(FIGURES_DIR / "03_population_map.png", "총인구 지도")
    unavailable(FIGURES_DIR / "04_youth_map.png", "청년인구 지도")
    unavailable(FIGURES_DIR / "05_elderly_map.png", "고령인구 지도")
    for number in range(1, 6):
        status[f"0{number}_population"] = DATA_NOT_AVAILABLE

    if capacity.empty:
        unavailable(FIGURES_DIR / "06_pond_distribution.png", "시설 저수용량 분포")
        status["06_pond_distribution"] = DATA_NOT_AVAILABLE
    else:
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.hist(capacity.dropna(), bins=20, color="#2f7658", edgecolor="white")
        ax.set_title("427개 시설 저수용량 분포")
        ax.set_xlabel("저수용량 (천톤)")
        ax.set_ylabel("시설 수")
        fig.tight_layout()
        fig.savefig(FIGURES_DIR / "06_pond_distribution.png", dpi=160)
        plt.close(fig)
        status["06_pond_distribution"] = "AVAILABLE"

    access = read_json(ANALYSIS_DIR / "pond_accessibility.json", {}) or {}
    if access.get("status") != "AVAILABLE":
        unavailable(FIGURES_DIR / "07_pond_road_accessibility.png", "못-도로 접근성")
        status["07_pond_road_accessibility"] = DATA_NOT_AVAILABLE
    else:
        values = [row.get("nearest_road_m") for row in access.get("data", []) if row.get("nearest_road_m") is not None]
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.hist(values, bins=20, color="#c9892e", edgecolor="white")
        ax.set_title("못-도로 최근접거리")
        ax.set_xlabel("거리 (m)")
        ax.set_ylabel("시설 수")
        fig.tight_layout()
        fig.savefig(FIGURES_DIR / "07_pond_road_accessibility.png", dpi=160)
        plt.close(fig)
        status["07_pond_road_accessibility"] = "AVAILABLE"

    context = read_json(ANALYSIS_DIR / "pond_context.json", {}) or {}
    if context.get("agricultural_status") != "AVAILABLE":
        unavailable(FIGURES_DIR / "08_pond_buffer_analysis.png", "500m·1km Buffer 농업지역")
        status["08_pond_buffer_analysis"] = DATA_NOT_AVAILABLE
    else:
        values_500 = [row.get("agricultural_area_ha_500m") for row in context.get("data", []) if row.get("agricultural_area_ha_500m") is not None]
        values_1000 = [row.get("agricultural_area_ha_1000m") for row in context.get("data", []) if row.get("agricultural_area_ha_1000m") is not None]
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.boxplot([values_500, values_1000], labels=["500m", "1km"])
        ax.set_title("못 주변 농업지역 면적")
        ax.set_ylabel("농업지역 (ha)")
        fig.tight_layout()
        fig.savefig(FIGURES_DIR / "08_pond_buffer_analysis.png", dpi=160)
        plt.close(fig)
        status["08_pond_buffer_analysis"] = "AVAILABLE"

    classification = read_json(ANALYSIS_DIR / "pond_classification_summary.json", {}) or {}
    types = classification.get("types", [])
    if not types:
        unavailable(FIGURES_DIR / "09_pond_classification.png", "못 활용유형 분류")
        status["09_pond_classification"] = DATA_NOT_AVAILABLE
    else:
        labels = [row["classification_type"] for row in types]
        counts = [row["facility_count"] for row in types]
        fig, ax = plt.subplots(figsize=(9, 4.5))
        ax.bar(labels, counts, color="#1f6049")
        ax.set_title("못 활용유형 분류 결과")
        ax.set_ylabel("시설 수")
        ax.tick_params(axis="x", rotation=20)
        fig.tight_layout()
        fig.savefig(FIGURES_DIR / "09_pond_classification.png", dpi=160)
        plt.close(fig)
        status["09_pond_classification"] = "AVAILABLE"

    fig, ax = plt.subplots(figsize=(11, 4))
    ax.axis("off")
    stages = ["원자료", "전처리", "공간분석", "규칙 기반 분류", "Web GIS"]
    for index, stage in enumerate(stages):
        x = 0.08 + index * 0.21
        ax.text(x, 0.52, stage, ha="center", va="center", fontsize=11, weight="bold", color="white", bbox={"boxstyle": "round,pad=0.8", "facecolor": "#1f6049", "edgecolor": "#c9892e"})
        if index < len(stages) - 1:
            ax.annotate("→", xy=(x + 0.105, 0.52), xytext=(x + 0.17, 0.52), ha="center", va="center", fontsize=20, color="#c9892e", arrowprops={"arrowstyle": "-"})
    ax.text(0.5, 0.18, "인구·도로·생활시설 원자료 확보 전에는 해당 지표를 DATA_NOT_AVAILABLE로 유지", ha="center", fontsize=10, color="#5d6d65")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "10_2025_2026_model_diagram.png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    status["10_2025_2026_model_diagram"] = "AVAILABLE"
    write_json(ANALYSIS_DIR / "figure_generation_status.json", status)
    return status


def main() -> None:
    result = run()
    print(f"그림 생성: {len(result)}개 상태 기록")


if __name__ == "__main__":
    main()


"""공모전 제출용 결과 묶음과 정량지표를 생성한다."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

try:
    from common import ANALYSIS_DIR, COMPETITION_DIR, DATA_NOT_AVAILABLE, GEOJSON_DIR, ensure_output_dirs, read_json, write_json
except ImportError:
    from analysis.common import ANALYSIS_DIR, COMPETITION_DIR, DATA_NOT_AVAILABLE, GEOJSON_DIR, ensure_output_dirs, read_json, write_json


def copy_json(source_name: str, target_name: str, fallback: dict) -> None:
    value = read_json(ANALYSIS_DIR / source_name, fallback)
    write_json(COMPETITION_DIR / target_name, value)


def run() -> dict:
    ensure_output_dirs()
    copy_json("population_summary.json", "population_summary.json", {"status": DATA_NOT_AVAILABLE, "data": []})
    copy_json("accessibility_summary.json", "accessibility_summary.json", {"status": DATA_NOT_AVAILABLE})
    copy_json("pond_context.json", "pond_context.json", {"status": DATA_NOT_AVAILABLE, "data": []})
    copy_json("traffic_culture_context.json", "traffic_culture_context.json", {"status": DATA_NOT_AVAILABLE, "datasets": []})
    copy_json("pond_classification.json", "pond_classification.json", {"status": DATA_NOT_AVAILABLE, "data": []})
    copy_json("pond_classification_summary.json", "pond_classification_summary.json", {"status": DATA_NOT_AVAILABLE})

    pond_path = Path("data/processed/ponds.csv")
    ponds = pd.read_csv(pond_path) if pond_path.exists() else pd.DataFrame()
    current_count = int(len(ponds))
    current_capacity = float(pd.to_numeric(ponds.iloc[:, 2], errors="coerce").sum()) if not ponds.empty else None
    metrics = {
        "status": "PARTIAL_DATASET_READY",
        "current_analyzed_facility_count": current_count,
        "legacy_metrics_preserved": {
            "raw_facility_count": 696,
            "analyzed_facility_count": 427,
            "total_capacity_thousand_ton": 39578.75,
            "mean_capacity_thousand_ton": 56.89,
            "mean_agricultural_area_1km_ha": 40.63,
            "spearman_capacity_agricultural_area_1km": 0.219,
        },
        "current_input_capacity_sum": current_capacity,
        "interpretation": "저수용량 하나만으로 주변 공간의 활용 가능성을 설명하기 어려워 인구·접근성·생활환경 결합이 필요함",
        "data_status": {
            "population": read_json(ANALYSIS_DIR / "population_input_status.json", {"status": DATA_NOT_AVAILABLE}).get("status", DATA_NOT_AVAILABLE),
            "vworld": read_json(ANALYSIS_DIR / "vworld_input_status.json", {"status": DATA_NOT_AVAILABLE}).get("status", DATA_NOT_AVAILABLE),
            "traffic_culture": read_json(ANALYSIS_DIR / "traffic_culture_context.json", {"status": DATA_NOT_AVAILABLE}).get("status", DATA_NOT_AVAILABLE),
        },
    }
    write_json(COMPETITION_DIR / "competition_metrics.json", metrics)
    return metrics


def main() -> None:
    result = run()
    print(f"공모전 결과 생성: {result['status']}")


if __name__ == "__main__":
    main()

"""읍·면 인구지표와 지도용 GeoJSON을 생성한다."""

from __future__ import annotations

import pandas as pd

try:
    from common import (
        ANALYSIS_DIR, DATA_NOT_AVAILABLE, GEOJSON_DIR, PROCESSED_DIR,
        ensure_output_dirs, frame_records, load_geojson, read_json, write_json,
    )
except ImportError:
    from analysis.common import (
        ANALYSIS_DIR, DATA_NOT_AVAILABLE, GEOJSON_DIR, PROCESSED_DIR,
        ensure_output_dirs, frame_records, load_geojson, read_json, write_json,
    )


def run() -> dict:
    ensure_output_dirs()
    source = PROCESSED_DIR / "population" / "uiseong_population.csv"
    status_info = read_json(ANALYSIS_DIR / "population_input_status.json", {}) or {}
    status = status_info.get("status", DATA_NOT_AVAILABLE)
    if not source.exists():
        population = pd.DataFrame()
    else:
        population = pd.read_csv(source)
    available = status == "AVAILABLE" and not population.empty

    if available:
        population["population_change_rate"] = population["population_change"] / (population["total_population"] - population["population_change"]) * 100
        population["population_change_rate"] = population["population_change_rate"].where(
            (population["total_population"] - population["population_change"]) != 0
        )
        records = frame_records(population)
        summary = {
            "status": "AVAILABLE",
            "year": sorted(population["year"].dropna().unique().tolist()),
            "emd_count": int(len(population)),
            "data": records,
        }
    else:
        summary = {
            "status": DATA_NOT_AVAILABLE,
            "year": [],
            "emd_count": 0,
            "data": [],
            "message": status_info.get("message", "인구 원자료가 없어 지표를 산출하지 않았습니다."),
        }

    write_json(ANALYSIS_DIR / "population_summary.json", summary)

    emd_path = GEOJSON_DIR / "uiseong_emd.geojson"
    if emd_path.exists():
        emd = load_geojson(emd_path)
        if available:
            emd = emd.merge(population, left_on="spatial_region", right_on="emd_name", how="left")
        emd["population_status"] = summary["status"]
        emd.to_file(GEOJSON_DIR / "population_by_emd.geojson", driver="GeoJSON", encoding="utf-8")
    return summary


def main() -> None:
    result = run()
    print(f"인구 분석: {result['status']}")


if __name__ == "__main__":
    main()


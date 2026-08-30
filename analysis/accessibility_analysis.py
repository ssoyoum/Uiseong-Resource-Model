"""못에서 가장 가까운 도로까지의 거리를 계산한다."""

from __future__ import annotations

import geopandas as gpd
import pandas as pd

try:
    from common import (
        ANALYSIS_CRS, ANALYSIS_DIR, DATA_NOT_AVAILABLE, GEOJSON_DIR,
        PROCESSED_DIR, ensure_output_dirs, frame_records, load_ponds, write_geojson, write_json,
    )
except ImportError:
    from analysis.common import (
        ANALYSIS_CRS, ANALYSIS_DIR, DATA_NOT_AVAILABLE, GEOJSON_DIR,
        PROCESSED_DIR, ensure_output_dirs, frame_records, load_ponds, write_geojson, write_json,
    )


def classify_distance(value):
    if pd.isna(value):
        return DATA_NOT_AVAILABLE
    if value <= 100:
        return "0–100m"
    if value <= 300:
        return "100–300m"
    if value <= 500:
        return "300–500m"
    return "500m 이상"


def run() -> pd.DataFrame:
    ensure_output_dirs()
    ponds = load_ponds(ANALYSIS_CRS)
    road_path = PROCESSED_DIR / "roads" / "uiseong_roads.gpkg"
    values = []
    status = "AVAILABLE" if road_path.exists() else DATA_NOT_AVAILABLE
    if road_path.exists():
        roads = gpd.read_file(road_path).to_crs(ANALYSIS_CRS)
        roads = roads.loc[roads.geometry.notna() & ~roads.geometry.is_empty]
        road_union = roads.geometry.union_all() if hasattr(roads.geometry, "union_all") else roads.geometry.unary_union
        for _, pond in ponds.iterrows():
            distance = float(pond.geometry.distance(road_union)) if not road_union.is_empty else None
            values.append({"pond_id": str(pond.id), "nearest_road_m": distance, "accessibility_class": classify_distance(distance)})
    else:
        values = [{"pond_id": str(pond.id), "nearest_road_m": None, "accessibility_class": DATA_NOT_AVAILABLE} for _, pond in ponds.iterrows()]

    result = pd.DataFrame(values)
    result.to_csv(ANALYSIS_DIR / "pond_accessibility.csv", index=False, encoding="utf-8-sig")
    summary = {
        "status": status,
        "facility_count": int(len(result)),
        "distance_unit": "meter" if status == "AVAILABLE" else DATA_NOT_AVAILABLE,
        "class_thresholds_m": [100, 300, 500] if status == "AVAILABLE" else None,
        "data": frame_records(result),
        "message": "도로 원자료가 없어 거리를 산출하지 않았습니다." if status != "AVAILABLE" else "EPSG:5174에서 점-도로 최소거리를 계산했습니다.",
    }
    write_json(ANALYSIS_DIR / "pond_accessibility.json", summary)
    write_json(ANALYSIS_DIR / "accessibility_summary.json", {
        "status": status,
        "facility_count": int(len(result)),
        "class_counts": result["accessibility_class"].value_counts(dropna=False).to_dict(),
        "mean_nearest_road_m": float(result["nearest_road_m"].mean()) if result["nearest_road_m"].notna().any() else None,
        "median_nearest_road_m": float(result["nearest_road_m"].median()) if result["nearest_road_m"].notna().any() else None,
    })
    geo = ponds.merge(result, left_on="id", right_on="pond_id", how="left")
    write_geojson(geo, GEOJSON_DIR / "ponds_accessibility.geojson")
    return result


def main() -> None:
    result = run()
    print(f"도로 접근성: {len(result)}개 시설 ({result['nearest_road_m'].notna().sum()}개 거리 산출)")


if __name__ == "__main__":
    main()

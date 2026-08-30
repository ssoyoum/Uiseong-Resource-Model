"""못 주변 500m·1km 공간조건을 EPSG:5174에서 계산한다."""

from __future__ import annotations

import geopandas as gpd
import pandas as pd

try:
    from common import (
        ANALYSIS_CRS, ANALYSIS_DIR, DATA_NOT_AVAILABLE, GEOJSON_DIR,
        PROCESSED_DIR, ensure_output_dirs, frame_records, load_geojson, load_ponds, read_json, write_geojson, write_json,
    )
except ImportError:
    from analysis.common import (
        ANALYSIS_CRS, ANALYSIS_DIR, DATA_NOT_AVAILABLE, GEOJSON_DIR,
        PROCESSED_DIR, ensure_output_dirs, frame_records, load_geojson, load_ponds, read_json, write_geojson, write_json,
    )


RADII = (500, 1000)


def load_optional_layer(paths: list) -> tuple[gpd.GeoDataFrame | None, str]:
    for path, source_name in paths:
        if not path.exists():
            continue
        layer = gpd.read_file(path).to_crs(ANALYSIS_CRS)
        layer = layer.loc[layer.geometry.notna() & ~layer.geometry.is_empty].copy()
        return layer, source_name
    return None, DATA_NOT_AVAILABLE


def nearest_emd_names(ponds: gpd.GeoDataFrame) -> pd.Series:
    path = GEOJSON_DIR / "uiseong_emd.geojson"
    if not path.exists():
        return pd.Series([None] * len(ponds), index=ponds.index)
    emd = load_geojson(path, ANALYSIS_CRS)
    joined = gpd.sjoin(ponds[["id", "geometry"]], emd[["spatial_region", "geometry"]], how="left", predicate="within")
    return joined.groupby(level=0)["spatial_region"].first().reindex(ponds.index)


def run() -> gpd.GeoDataFrame:
    ensure_output_dirs()
    ponds = load_ponds(ANALYSIS_CRS)
    ponds["emd_name"] = nearest_emd_names(ponds)
    agri_path = GEOJSON_DIR / "agricultural_areas.geojson"
    agri = load_geojson(agri_path, ANALYSIS_CRS) if agri_path.exists() else None
    agri = agri.loc[agri.geometry.notna() & ~agri.geometry.is_empty] if agri is not None else None
    facilities, facility_source = load_optional_layer([
        (PROCESSED_DIR / "facilities" / "uiseong_facilities.gpkg", "VWorld UQ164·UO601"),
        (PROCESSED_DIR / "facilities" / "uiseong_osm_facilities.gpkg", "OpenStreetMap"),
    ])
    roads, road_source = load_optional_layer([
        (PROCESSED_DIR / "roads" / "uiseong_roads.gpkg", "VWorld UQ151"),
        (PROCESSED_DIR / "roads" / "uiseong_osm_roads.gpkg", "OpenStreetMap"),
    ])
    population_path = PROCESSED_DIR / "population" / "uiseong_population.csv"
    population = pd.read_csv(population_path) if population_path.exists() else pd.DataFrame()
    population = population.set_index("emd_name") if not population.empty and "emd_name" in population else population
    rows = []
    for _, pond in ponds.iterrows():
        item = {"pond_id": str(pond.id), "address": pond.get("address"), "region": pond.get("region"), "emd_name": pond.get("emd_name"), "capacity": pond.get("capacity")}
        item["facility_source"] = facility_source
        item["road_source"] = road_source
        if not population.empty and pond.get("emd_name") in population.index:
            population_row = population.loc[pond.get("emd_name")]
            for column in ("total_population", "youth_population", "elderly_population", "youth_ratio", "elderly_ratio", "population_change", "year"):
                item[f"emd_{column}"] = population_row.get(column)
            item["population_context_method"] = "pond_emd_population_context"
        else:
            item["population_context_method"] = DATA_NOT_AVAILABLE
        for radius in RADII:
            buffer = pond.geometry.buffer(radius)
            prefix = f"{radius}m"
            item[f"population_{prefix}"] = None
            item[f"youth_population_{prefix}"] = None
            item[f"elderly_population_{prefix}"] = None
            item[f"facility_count_{prefix}"] = None
            item[f"road_length_{prefix}"] = None
            item[f"population_context_method_{prefix}"] = item["population_context_method"]
            if agri is None:
                item[f"agricultural_area_{prefix}"] = None
                item[f"agricultural_area_ha_{prefix}"] = None
                item[f"agricultural_ratio_{prefix}"] = None
            else:
                candidates = agri.iloc[list(agri.sindex.query(buffer, predicate="intersects"))]
                area = sum(geometry.intersection(buffer).area for geometry in candidates.geometry if not geometry.is_empty)
                item[f"agricultural_area_{prefix}"] = float(area)
                item[f"agricultural_area_ha_{prefix}"] = float(area / 10000)
                item[f"agricultural_ratio_{prefix}"] = float(area / buffer.area * 100)
            if facilities is not None:
                facility_indices = facilities.sindex.query(buffer, predicate="intersects")
                item[f"facility_count_{prefix}"] = int(len(facility_indices))
            if roads is not None:
                road_indices = roads.sindex.query(buffer, predicate="intersects")
                road_candidates = roads.iloc[list(road_indices)]
                item[f"road_length_{prefix}"] = float(sum(
                    geometry.intersection(buffer).length
                    for geometry in road_candidates.geometry
                    if not geometry.is_empty
                ))
        rows.append(item)

    result = pd.DataFrame(rows)
    result.to_csv(ANALYSIS_DIR / "pond_context.csv", index=False, encoding="utf-8-sig")
    write_json(ANALYSIS_DIR / "pond_emd_population_context.json", {
        "status": "AVAILABLE" if not population.empty else DATA_NOT_AVAILABLE,
        "method": "읍·면 통계를 못 위치에 연결한 참고정보; Buffer 내부 인구로 배분하지 않음",
        "data": frame_records(result[[column for column in result.columns if column.startswith("pond_id") or column.startswith("emd_") or column == "population_context_method"]]),
    })
    write_json(ANALYSIS_DIR / "pond_context.json", {
        "status": "AVAILABLE" if agri is not None else DATA_NOT_AVAILABLE,
        "population_status": "EMD_AGGREGATE_ONLY" if not population.empty else DATA_NOT_AVAILABLE,
        "roads_status": "AVAILABLE" if roads is not None else DATA_NOT_AVAILABLE,
        "road_source": road_source,
        "facilities_status": "AVAILABLE" if facilities is not None else DATA_NOT_AVAILABLE,
        "facility_source": facility_source,
        "facility_feature_count": int(len(facilities)) if facilities is not None else 0,
        "agricultural_status": "AVAILABLE" if agri is not None else DATA_NOT_AVAILABLE,
        "distance_unit": "meter",
        "area_unit": "m² and ha",
        "data": frame_records(result),
        "message": "읍·면 집계만으로 Buffer 내 인구를 배분하지 않았습니다.",
    })

    output = ponds[["id", "address", "region", "capacity", "emd_name", "geometry"]].copy()
    output = output.merge(result.drop(columns=["address", "region", "capacity", "emd_name"]), left_on="id", right_on="pond_id", how="left")
    write_geojson(output, GEOJSON_DIR / "ponds_context.geojson")
    return output


def main() -> None:
    result = run()
    print(f"못 주변 생활권: {len(result)}개 시설")


if __name__ == "__main__":
    main()

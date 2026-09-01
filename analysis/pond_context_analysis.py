"""못 주변 500m·1km 공간조건을 EPSG:5174에서 계산한다."""

from __future__ import annotations

import re

import geopandas as gpd
import pandas as pd

try:
    from common import (
    ANALYSIS_CRS, ANALYSIS_DIR, BASE_DIR, DATA_NOT_AVAILABLE, GEOJSON_DIR,
        PROCESSED_DIR, RAW_DIR, ensure_output_dirs, frame_records, load_geojson, load_ponds, read_json, write_geojson, write_json,
    )
except ImportError:
    from analysis.common import (
    ANALYSIS_CRS, ANALYSIS_DIR, BASE_DIR, DATA_NOT_AVAILABLE, GEOJSON_DIR,
        PROCESSED_DIR, RAW_DIR, ensure_output_dirs, frame_records, load_geojson, load_ponds, read_json, write_geojson, write_json,
    )


RADII = (500, 1000)
SGIS_CATCHMENT_PATH = PROCESSED_DIR / "population" / "sgis_drive_population.csv"


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


def _column_by_alias(frame: gpd.GeoDataFrame, aliases: tuple[str, ...]) -> str | None:
    normalized = {
        re.sub(r"[^A-Z0-9]", "", str(column).upper()): column
        for column in frame.columns
    }
    for alias in aliases:
        column = normalized.get(re.sub(r"[^A-Z0-9]", "", alias.upper()))
        if column is not None:
            return column
    return None


def load_official_population_grid() -> tuple[gpd.GeoDataFrame | None, dict[str, str]]:
    """Load an explicitly supplied official population grid, if present.

    Only vector files in an ``official_grid`` or ``sgis`` directory are
    considered. This prevents administrative totals and WorldPop rasters
    from being mistaken for an official spatial population grid.
    """
    population_root = RAW_DIR / "population"
    candidates = [
        path
        for path in population_root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in {".gpkg", ".shp", ".geojson", ".json"}
        and any(token in {part.lower() for part in path.parts} for token in {"official_grid", "sgis"})
    ] if population_root.exists() else []
    for path in sorted(candidates):
        try:
            grid = gpd.read_file(path)
            if grid.crs is None:
                continue
            grid = grid.to_crs(ANALYSIS_CRS)
            grid = grid.loc[grid.geometry.notna() & ~grid.geometry.is_empty].copy()
            total_column = _column_by_alias(
                grid,
                ("population", "total_population", "tot_ppltn", "tot_pop", "pop_count"),
            )
            if total_column is None or grid.empty:
                continue
            metadata = {
                "status": "AVAILABLE",
                "source": str(path.relative_to(RAW_DIR.parent.parent)).replace("\\", "/"),
                "reference_year": "",
                "total_column": total_column,
                "youth_column": _column_by_alias(
                    grid, ("youth_population", "youth_pop", "young_population")
                ) or "",
                "elderly_column": _column_by_alias(
                    grid, ("elderly_population", "elderly_pop", "aged_population")
                ) or "",
            }
            year_column = _column_by_alias(grid, ("reference_year", "base_year", "year"))
            if year_column:
                years = grid[year_column].dropna().astype(str).unique().tolist()
                metadata["reference_year"] = years[0] if len(years) == 1 else ",".join(years)
            return grid, metadata
        except Exception:
            continue
    return None, {"status": DATA_NOT_AVAILABLE, "source": "", "reference_year": ""}


def load_sgis_catchment() -> tuple[pd.DataFrame | None, dict[str, object]]:
    """Load SGIS route-catchment results as a separate auxiliary metric."""
    if not SGIS_CATCHMENT_PATH.exists():
        return None, {"status": DATA_NOT_AVAILABLE, "source": "", "year": None}
    try:
        frame = pd.read_csv(SGIS_CATCHMENT_PATH, dtype={"pond_id": str})
        required = {"pond_id", "sgis_year", "drive_time_min", "sgis_population", "status"}
        if not required.issubset(frame.columns):
            return None, {"status": DATA_NOT_AVAILABLE, "source": str(SGIS_CATCHMENT_PATH), "year": None}
        frame["pond_id"] = frame["pond_id"].astype(str)
        frame["drive_time_min"] = pd.to_numeric(frame["drive_time_min"], errors="coerce")
        frame["sgis_population"] = pd.to_numeric(frame["sgis_population"], errors="coerce")
        years = frame["sgis_year"].dropna().astype(str).unique().tolist()
        return frame, {
            "status": "AVAILABLE" if (frame["status"] == "AVAILABLE").any() else DATA_NOT_AVAILABLE,
            "source": str(SGIS_CATCHMENT_PATH.relative_to(BASE_DIR)).replace("\\", "/"),
            "year": years[0] if len(years) == 1 else ",".join(years),
        }
    except Exception:
        return None, {"status": DATA_NOT_AVAILABLE, "source": str(SGIS_CATCHMENT_PATH), "year": None}


def grid_population_in_buffer(
    grid: gpd.GeoDataFrame,
    buffer,
    column: str,
) -> float | None:
    """Area-weight population cells intersecting a metric buffer."""
    if not column or column not in grid.columns:
        return None
    indices = grid.sindex.query(buffer, predicate="intersects")
    total = 0.0
    has_value = False
    for index in indices:
        cell = grid.iloc[index]
        if cell.geometry is None or cell.geometry.is_empty or cell.geometry.area <= 0:
            continue
        value = pd.to_numeric(cell[column], errors="coerce")
        if pd.isna(value):
            continue
        intersection_area = cell.geometry.intersection(buffer).area
        if intersection_area <= 0:
            continue
        total += float(value) * float(intersection_area / cell.geometry.area)
        has_value = True
    return total if has_value else None


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
    population_grid, population_grid_info = load_official_population_grid()
    sgis_catchment, sgis_info = load_sgis_catchment()
    rows = []
    for _, pond in ponds.iterrows():
        item = {"pond_id": str(pond.id), "address": pond.get("address"), "region": pond.get("region"), "emd_name": pond.get("emd_name"), "capacity": pond.get("capacity")}
        item["facility_source"] = facility_source
        item["road_source"] = road_source
        for drive_minutes in (5, 10):
            item[f"sgis_drive_population_{drive_minutes}min"] = None
            item[f"sgis_drive_population_{drive_minutes}min_status"] = DATA_NOT_AVAILABLE
        if sgis_catchment is not None:
            sgis_rows = sgis_catchment[
                (sgis_catchment["pond_id"] == str(pond.id))
                & (sgis_catchment["status"] == "AVAILABLE")
            ]
            for drive_minutes in (5, 10):
                match = sgis_rows[sgis_rows["drive_time_min"] == drive_minutes]
                if not match.empty:
                    item[f"sgis_drive_population_{drive_minutes}min"] = match.iloc[-1]["sgis_population"]
                    item[f"sgis_drive_population_{drive_minutes}min_status"] = "AVAILABLE"
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
            item[f"official_population_{'500m' if radius == 500 else '1km'}"] = None
            item[f"youth_population_{prefix}"] = None
            item[f"official_youth_population_{'500m' if radius == 500 else '1km'}"] = None
            item[f"elderly_population_{prefix}"] = None
            item[f"official_elderly_population_{'500m' if radius == 500 else '1km'}"] = None
            if radius == 1000:
                item["population_1km"] = None
                item["youth_population_1km"] = None
                item["elderly_population_1km"] = None
            item[f"facility_count_{prefix}"] = None
            item[f"road_length_{prefix}"] = None
            item[f"population_context_method_{prefix}"] = item["population_context_method"]
            if population_grid is not None:
                grid_suffix = "500m" if radius == 500 else "1km"
                total = grid_population_in_buffer(
                    population_grid, buffer, population_grid_info["total_column"]
                )
                youth = grid_population_in_buffer(
                    population_grid, buffer, population_grid_info["youth_column"]
                )
                elderly = grid_population_in_buffer(
                    population_grid, buffer, population_grid_info["elderly_column"]
                )
                item[f"population_{prefix}"] = total
                item[f"official_population_{grid_suffix}"] = total
                item[f"youth_population_{prefix}"] = youth
                item[f"official_youth_population_{grid_suffix}"] = youth
                item[f"elderly_population_{prefix}"] = elderly
                item[f"official_elderly_population_{grid_suffix}"] = elderly
                if radius == 1000:
                    item["population_1km"] = total
                    item["youth_population_1km"] = youth
                    item["elderly_population_1km"] = elderly
                item[f"population_context_method_{prefix}"] = "official_grid_area_weighted_intersection"
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
        "population_status": (
            "OFFICIAL_GRID_AREA_WEIGHTED"
            if population_grid is not None
            else "EMD_AGGREGATE_ONLY" if not population.empty else DATA_NOT_AVAILABLE
        ),
        "population_grid_status": population_grid_info["status"],
        "population_grid_source": population_grid_info["source"],
        "population_grid_reference_year": population_grid_info["reference_year"],
        "sgis_catchment_status": sgis_info["status"],
        "sgis_catchment_source": sgis_info["source"],
        "sgis_catchment_year": sgis_info["year"],
        "sgis_catchment_metric": "route-based service-area population; separate from official-grid Buffer population",
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

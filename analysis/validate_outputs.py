"""공모전 파이프라인 결과의 기본 공간·데이터 검증."""

from __future__ import annotations

import math
from pathlib import Path

import geopandas as gpd

try:
    from common import ANALYSIS_CRS, ANALYSIS_DIR, DATA_NOT_AVAILABLE, GEOJSON_DIR, PROCESSED_DIR, ensure_output_dirs, load_ponds, read_json, write_json
except ImportError:
    from analysis.common import ANALYSIS_CRS, ANALYSIS_DIR, DATA_NOT_AVAILABLE, GEOJSON_DIR, PROCESSED_DIR, ensure_output_dirs, load_ponds, read_json, write_json


def check(name, status, details=None):
    return {"name": name, "status": status, "details": details or {}}


def run() -> dict:
    ensure_output_dirs()
    checks = []
    ponds = load_ponds(ANALYSIS_CRS)
    boundary = gpd.read_file(GEOJSON_DIR / "uiseong_boundary.geojson")
    if boundary.crs is None:
        boundary = boundary.set_crs("EPSG:4326")
    boundary = boundary.to_crs(ANALYSIS_CRS)
    boundary_union = boundary.geometry.union_all() if hasattr(boundary.geometry, "union_all") else boundary.geometry.unary_union

    checks.append(check("pond_count_427", "PASS" if len(ponds) == 427 else "FAIL", {"actual": len(ponds), "expected": 427}))
    checks.append(check("pond_geometry_valid", "PASS" if bool(ponds.geometry.is_valid.all()) else "FAIL", {"invalid_count": int((~ponds.geometry.is_valid).sum())}))
    checks.append(check("pond_id_duplicate", "PASS" if not ponds.id.duplicated().any() else "WARN", {"duplicate_count": int(ponds.id.duplicated().sum())}))
    checks.append(check("pond_coordinate_duplicate", "PASS" if not ponds.geometry.duplicated().any() else "WARN", {"duplicate_count": int(ponds.geometry.duplicated().sum())}))
    checks.append(check("pond_required_null", "PASS" if not ponds[["id", "capacity", "geometry"]].isna().any().any() else "WARN", {"null_counts": ponds[["id", "capacity", "geometry"]].isna().sum().to_dict()}))
    outside = ~ponds.geometry.map(boundary_union.covers)
    checks.append(check("ponds_inside_uiseong_boundary", "PASS" if not outside.any() else "FAIL", {"outside_count": int(outside.sum())}))
    checks.append(check("analysis_crs_meter", "PASS" if ponds.crs.to_string() == ANALYSIS_CRS else "FAIL", {"crs": ponds.crs.to_string(), "expected": ANALYSIS_CRS}))

    facilities_path = PROCESSED_DIR / "facilities" / "uiseong_facilities.gpkg"
    if facilities_path.exists():
        facilities = gpd.read_file(facilities_path).to_crs(ANALYSIS_CRS)
        # Clipping can leave sub-millimetre floating-point slivers on the
        # boundary. Allow a 1 cm tolerance for the containment check while
        # retaining the strict geometry validation above.
        facility_boundary_tolerance_m = 0.01
        facility_boundary_check = boundary_union.buffer(facility_boundary_tolerance_m)
        facility_outside = ~facilities.geometry.map(facility_boundary_check.covers)
        checks.append(check("vworld_facilities_crs", "PASS" if facilities.crs.to_string() == ANALYSIS_CRS else "FAIL", {"crs": facilities.crs.to_string(), "expected": ANALYSIS_CRS}))
        checks.append(check("vworld_facilities_geometry_valid", "PASS" if bool(facilities.geometry.is_valid.all()) else "FAIL", {"invalid_count": int((~facilities.geometry.is_valid).sum())}))
        checks.append(check("vworld_facilities_inside_boundary", "PASS" if not facility_outside.any() else "FAIL", {"feature_count": len(facilities), "outside_count": int(facility_outside.sum()), "boundary_tolerance_m": facility_boundary_tolerance_m}))
    else:
        checks.append(check("vworld_facilities", DATA_NOT_AVAILABLE, {"message": "VWorld 시설 원자료 미확보"}))

    roads_path = PROCESSED_DIR / "roads" / "uiseong_roads.gpkg"
    if roads_path.exists():
        roads = gpd.read_file(roads_path, layer="roads").to_crs(ANALYSIS_CRS)
        road_boundary_tolerance_m = 0.01
        road_boundary_check = boundary_union.buffer(road_boundary_tolerance_m)
        road_outside = ~roads.geometry.map(road_boundary_check.covers)
        checks.append(check("vworld_roads_crs", "PASS" if roads.crs.to_string() == ANALYSIS_CRS else "FAIL", {"crs": roads.crs.to_string(), "expected": ANALYSIS_CRS}))
        checks.append(check("vworld_roads_geometry_valid", "PASS" if bool(roads.geometry.is_valid.all()) else "FAIL", {"invalid_count": int((~roads.geometry.is_valid).sum())}))
        checks.append(check("vworld_roads_inside_boundary", "PASS" if not road_outside.any() else "FAIL", {"feature_count": len(roads), "outside_count": int(road_outside.sum()), "boundary_tolerance_m": road_boundary_tolerance_m}))
    else:
        checks.append(check("vworld_roads", DATA_NOT_AVAILABLE, {"message": "VWorld UQ151 도로 원자료 미확보"}))

    access = read_json(ANALYSIS_DIR / "pond_accessibility.json", {}) or {}
    if access.get("status") == DATA_NOT_AVAILABLE:
        checks.append(check("distance_unit_meter", "DATA_NOT_AVAILABLE", {"message": "도로 원자료 없음"}))
    else:
        checks.append(check("distance_unit_meter", "PASS" if access.get("distance_unit") == "meter" else "FAIL", {"unit": access.get("distance_unit")}))

    context = read_json(ANALYSIS_DIR / "pond_context.json", {}) or {}
    values = [row.get("agricultural_area_ha_1000m") for row in context.get("data", []) if row.get("agricultural_area_ha_1000m") is not None]
    checks.append(check("buffer_area_unit", "PASS" if context.get("area_unit") == "m² and ha" and all(value >= 0 for value in values) else "WARN", {"unit": context.get("area_unit"), "record_count": len(values)}))
    emd_path = GEOJSON_DIR / "uiseong_emd.geojson"
    if emd_path.exists():
        emd = gpd.read_file(emd_path)
        if emd.crs is None:
            emd = emd.set_crs("EPSG:4326")
        checks.append(check("emd_geometry_valid", "PASS" if bool(emd.geometry.is_valid.all()) else "FAIL", {"invalid_count": int((~emd.geometry.is_valid).sum())}))
        checks.append(check("spatial_join_missing", "PASS" if "spatial_region" in emd and not emd.spatial_region.isna().any() else "WARN", {"missing_count": int(emd.spatial_region.isna().sum()) if "spatial_region" in emd else None}))

    passed = sum(item["status"] == "PASS" for item in checks)
    failed = sum(item["status"] == "FAIL" for item in checks)
    report = {
        "status": "PASS" if failed == 0 else "FAIL",
        "pass_count": passed,
        "fail_count": failed,
        "checks": checks,
        "note": "DATA_NOT_AVAILABLE는 오류가 아니라 원자료 미확보 상태를 뜻합니다.",
    }
    write_json(ANALYSIS_DIR / "validation_report.json", report)
    return report


def main() -> None:
    result = run()
    print(f"검증: {result['status']} (pass={result['pass_count']}, fail={result['fail_count']})")


if __name__ == "__main__":
    main()

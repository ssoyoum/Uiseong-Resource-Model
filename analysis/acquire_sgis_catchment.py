"""Acquire SGIS route-based population for the Uiseong facility points."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd
from pyproj import Transformer

try:
    from common import ANALYSIS_CRS, BASE_DIR, apply_coordinate_corrections, load_ponds, write_json
    from sgis_api import SgisApiError, SgisNoDataError, authenticate, service_area_geometry, service_area_statistics
except ImportError:
    from analysis.common import ANALYSIS_CRS, BASE_DIR, apply_coordinate_corrections, load_ponds, write_json
    from analysis.sgis_api import SgisApiError, SgisNoDataError, authenticate, service_area_geometry, service_area_statistics


OUTPUT_PATH = BASE_DIR / "data" / "processed" / "population" / "sgis_drive_population.csv"
STATUS_PATH = BASE_DIR / "data" / "analysis" / "sgis_catchment_status.json"
TARGET_CRS = "EPSG:5179"


def polygon_wkt(feature: dict[str, Any]) -> str:
    rings = feature.get("geometry", {}).get("rings", [])
    if not rings:
        raise SgisApiError("SGIS route polygon has no rings")
    encoded_rings = []
    for ring in rings:
        encoded_rings.append(",".join(f"{float(point[0])} {float(point[1])}" for point in ring))
    return "POLYGON(" + ",".join(f"({ring})" for ring in encoded_rings) + ")"


def choose_feature(features: list[dict[str, Any]], minutes: int) -> dict[str, Any]:
    target_break = max(1, minutes * 60 - 4)
    return min(
        features,
        key=lambda feature: abs(
            float((feature.get("attributes") or {}).get("ToBreak", target_break)) - target_break
        ),
    )


def population_record(payload: dict[str, Any]) -> tuple[int | None, int | None, float | None]:
    result = payload.get("result") or {}
    rows = result.get("pops") or []
    row = rows[0] if rows and isinstance(rows[0], dict) else {}
    displayed = row.get("popsTotOgl")
    api_total = row.get("tot_ppltn_cnt")
    area_rows = result.get("areaSize") or []
    area = area_rows[0].get("area_size") if area_rows else None
    return (
        int(float(displayed)) if displayed not in (None, "") else None,
        int(float(api_total)) if api_total not in (None, "") else None,
        float(area) if area not in (None, "") else None,
    )


def load_existing() -> pd.DataFrame:
    if not OUTPUT_PATH.exists():
        return pd.DataFrame()
    frame = pd.read_csv(OUTPUT_PATH, dtype={"pond_id": str, "drive_time_min": int, "sgis_year": int})
    keys = ["pond_id", "sgis_year", "drive_time_min"]
    if set(keys).issubset(frame.columns):
        frame = frame.drop_duplicates(subset=keys, keep="last")
    return frame


def write_rows(rows: list[dict[str, Any]]) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(rows)
    keys = ["pond_id", "sgis_year", "drive_time_min"]
    if set(keys).issubset(frame.columns):
        frame = frame.drop_duplicates(subset=keys, keep="last")
    frame.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")


def run(year: int = 2024, minutes: list[int] | None = None, limit: int | None = None, delay: float = 0.2) -> dict[str, Any]:
    minutes = sorted(set(minutes or [5, 10]))
    ponds = apply_coordinate_corrections(load_ponds(ANALYSIS_CRS))
    if limit is not None:
        ponds = ponds.head(limit)
    transformer = Transformer.from_crs(ANALYSIS_CRS, TARGET_CRS, always_xy=True)
    token, _ = authenticate()
    existing = load_existing()
    completed = {
        (str(row.pond_id), int(row.drive_time_min), int(row.sgis_year))
        for row in existing.itertuples()
        if str(getattr(row, "status", "")) in {"AVAILABLE", "DATA_NOT_AVAILABLE"}
    } if not existing.empty and "sgis_year" in existing.columns else set()
    rows = existing.to_dict(orient="records") if not existing.empty else []
    status_counts: dict[str, int] = {}

    def append_unavailable(pond_id: str, status: str, error: str) -> None:
        for drive_minutes in minutes:
            if (pond_id, drive_minutes, year) not in completed:
                rows.append(
                    {
                        "pond_id": pond_id,
                        "sgis_year": year,
                        "drive_time_min": drive_minutes,
                        "sgis_population": None,
                        "sgis_population_api_total": None,
                        "service_area_m2": None,
                        "source": "SGIS 생활권역 통계지도 serviceAreaStatistics",
                        "source_endpoint": "https://sgis.mods.go.kr/ServiceAPI/OpenAPI3/catchmentArea/serviceAreaStatistics.json",
                        "coordinate_crs": TARGET_CRS,
                        "status": status,
                        "error": error,
                    }
                )
                status_counts[status] = status_counts.get(status, 0) + 1

    for idx, pond in ponds.iterrows():
        pond_id = str(pond["id"])
        centroid = pond.geometry.centroid
        x, y = transformer.transform(float(centroid.x), float(centroid.y))
        try:
            geometry_payload = service_area_geometry(token, x, y, minutes)
            for drive_minutes in minutes:
                key = (pond_id, drive_minutes, year)
                if key in completed:
                    continue
                feature = choose_feature(geometry_payload["features"], drive_minutes)
                stats_payload = service_area_statistics(token, polygon_wkt(feature), year)
                population, api_total, area_m2 = population_record(stats_payload)
                rows.append(
                    {
                        "pond_id": pond_id,
                        "sgis_year": year,
                        "drive_time_min": drive_minutes,
                        "sgis_population": population,
                        "sgis_population_api_total": api_total,
                        "service_area_m2": area_m2,
                        "source": "SGIS 생활권역 통계지도 serviceAreaStatistics",
                        "source_endpoint": "https://sgis.mods.go.kr/ServiceAPI/OpenAPI3/catchmentArea/serviceAreaStatistics.json",
                        "coordinate_crs": TARGET_CRS,
                        "status": "AVAILABLE" if population is not None else "DATA_NOT_AVAILABLE",
                    }
                )
                status_counts["AVAILABLE" if population is not None else "DATA_NOT_AVAILABLE"] = status_counts.get(
                    "AVAILABLE" if population is not None else "DATA_NOT_AVAILABLE", 0
                ) + 1
                time.sleep(delay)
        except SgisNoDataError as exc:
            append_unavailable(pond_id, "DATA_NOT_AVAILABLE", str(exc))
        except (SgisApiError, ValueError, TypeError) as exc:
            append_unavailable(pond_id, "ERROR", str(exc))
        write_rows(rows)
        if (idx + 1) % 10 == 0 or idx == len(ponds) - 1:
            print(f"processed={idx + 1}/{len(ponds)} rows={len(rows)}")

    final_frame = pd.DataFrame(rows)
    keys = ["pond_id", "sgis_year", "drive_time_min"]
    if set(keys).issubset(final_frame.columns):
        final_frame = final_frame.drop_duplicates(subset=keys, keep="last")
    final_counts = final_frame["status"].value_counts().to_dict() if "status" in final_frame.columns else {}
    status = {
        "status": "PASS" if final_counts.get("ERROR", 0) == 0 else "PARTIAL",
        "year": year,
        "drive_times_min": minutes,
        "requested_facilities": len(ponds),
        "output": str(OUTPUT_PATH.relative_to(BASE_DIR)).replace("\\", "/"),
        "counts": {str(key): int(value) for key, value in final_counts.items()},
        "privacy_note": "SGIS 생활권역 값은 비밀보호 처리된 서비스 제공값이며 실제값과 차이가 있을 수 있음",
    }
    write_json(STATUS_PATH, status)
    return status


def main() -> None:
    parser = argparse.ArgumentParser(description="Acquire SGIS driving-catchment population")
    parser.add_argument("--year", type=int, default=2024)
    parser.add_argument("--minutes", nargs="+", type=int, default=[5, 10])
    parser.add_argument("--limit", type=int, default=None, help="process only the first N facilities")
    parser.add_argument("--delay", type=float, default=0.2)
    args = parser.parse_args()
    status = run(args.year, args.minutes, args.limit, args.delay)
    print(json.dumps(status, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

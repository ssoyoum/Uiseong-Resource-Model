"""WorldPop 100m 격자로 못 주변 500m·1km 참고 인구를 계산한다.

WorldPop은 국내 공식 인구격자를 대체하지 않는다. 결과는 worldpop_* 필드로만
별도 파일에 저장하고 official_population_* 필드나 pond_context에는 넣지 않는다.
격자 중심점이 Buffer 안에 있는 셀의 값을 합산한다(면적가중 아님).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import tifffile
from pyproj import Transformer

try:
    from common import ANALYSIS_CRS, ANALYSIS_DIR, BASE_DIR, DATA_NOT_AVAILABLE, RAW_DIR, ensure_output_dirs, load_ponds, write_json
except ImportError:
    from analysis.common import ANALYSIS_CRS, ANALYSIS_DIR, BASE_DIR, DATA_NOT_AVAILABLE, RAW_DIR, ensure_output_dirs, load_ponds, write_json


RASTER_PATH = RAW_DIR / "population" / "worldpop" / "kor_pop_2020_CN_100m_R2025A_v1.tif"
RADII = {500: "500m", 1000: "1km"}
REFERENCE_YEAR = "2020"
WINDOW_MARGIN_DEG = 0.05
GEOGRAPHIC_TYPE_GEOKEY = 2048
PROJECTED_CS_TYPE_GEOKEY = 3072


def raster_crs(page) -> str | None:
    keys = page.tags.get("GeoKeyDirectoryTag")
    if keys is None:
        return None
    values = list(keys.value)
    for offset in range(4, len(values), 4):
        key_id, location, _, code = values[offset:offset + 4]
        if location == 0 and key_id in (PROJECTED_CS_TYPE_GEOKEY, GEOGRAPHIC_TYPE_GEOKEY):
            return f"EPSG:{code}"
    return None


def read_window(bounds: tuple[float, float, float, float]) -> dict:
    """bounds(lon_min, lat_min, lon_max, lat_max)를 덮는 격자창을 읽는다."""
    with tifffile.TiffFile(RASTER_PATH) as tif:
        page = tif.pages[0]
        crs = raster_crs(page)
        scale_x, scale_y = page.tags["ModelPixelScaleTag"].value[:2]
        _, _, _, origin_x, origin_y, _ = page.tags["ModelTiepointTag"].value[:6]
        nodata_tag = page.tags.get("GDAL_NODATA")
        nodata = float(str(nodata_tag.value).strip("\x00 ")) if nodata_tag is not None else None
        lon_min, lat_min, lon_max, lat_max = bounds
        col0 = max(int(np.floor((lon_min - origin_x) / scale_x)), 0)
        col1 = min(int(np.ceil((lon_max - origin_x) / scale_x)), page.imagewidth)
        row0 = max(int(np.floor((origin_y - lat_max) / scale_y)), 0)
        row1 = min(int(np.ceil((origin_y - lat_min) / scale_y)), page.imagelength)
        data = page.asarray()[row0:row1, col0:col1].astype("float64")
    if nodata is not None:
        data[data == nodata] = np.nan
    data[data < 0] = np.nan
    lon = origin_x + (np.arange(col0, col1) + 0.5) * scale_x
    lat = origin_y - (np.arange(row0, row1) + 0.5) * scale_y
    return {"crs": crs, "data": data, "lon": lon, "lat": lat, "scale": (scale_x, scale_y), "nodata": nodata}


def unavailable(message: str) -> dict:
    result = {"status": DATA_NOT_AVAILABLE, "message": message}
    write_json(ANALYSIS_DIR / "worldpop_reference_buffer.json", result)
    return result


def run() -> dict:
    ensure_output_dirs()
    if not RASTER_PATH.exists():
        return unavailable("WorldPop 원자료 미확보: python analysis/acquire_worldpop.py")

    ponds = load_ponds(ANALYSIS_CRS)
    to_wgs84 = Transformer.from_crs(ANALYSIS_CRS, "EPSG:4326", always_xy=True)
    lon_min, lat_min, lon_max, lat_max = ponds.to_crs("EPSG:4326").total_bounds
    try:
        window = read_window((
            lon_min - WINDOW_MARGIN_DEG, lat_min - WINDOW_MARGIN_DEG,
            lon_max + WINDOW_MARGIN_DEG, lat_max + WINDOW_MARGIN_DEG,
        ))
    except ValueError as exc:  # 예: LZW 압축 해제에 imagecodecs가 없을 때
        return unavailable(f"WorldPop 격자를 읽지 못함: {exc}")
    if window["crs"] != "EPSG:4326":
        return unavailable(f"예상하지 않은 WorldPop CRS: {window['crs']}")

    lon_grid, lat_grid = np.meshgrid(window["lon"], window["lat"])
    to_analysis = Transformer.from_crs("EPSG:4326", ANALYSIS_CRS, always_xy=True)
    center_x, center_y = to_analysis.transform(lon_grid, lat_grid)
    values = window["data"]

    rows = []
    for _, pond in ponds.iterrows():
        x, y = pond.geometry.x, pond.geometry.y
        distance = np.hypot(center_x - x, center_y - y)
        item = {"pond_id": str(pond.id)}
        for radius, suffix in RADII.items():
            inside = distance <= radius
            cell_values = values[inside]
            valid = cell_values[~np.isnan(cell_values)]
            item[f"worldpop_population_{suffix}"] = float(valid.sum()) if valid.size else 0.0
            item[f"worldpop_cell_count_{suffix}"] = int(inside.sum())
            item[f"worldpop_populated_cell_count_{suffix}"] = int(valid.size)
        rows.append(item)
    result = pd.DataFrame(rows)
    result["worldpop_reference_year"] = REFERENCE_YEAR
    result["worldpop_status"] = "REFERENCE_ONLY"
    result.to_csv(ANALYSIS_DIR / "worldpop_reference_buffer.csv", index=False, encoding="utf-8-sig")

    summary = {
        "status": "REFERENCE_ONLY",
        "source": str(RASTER_PATH.relative_to(BASE_DIR)).replace("\\", "/"),
        "source_manifest": "data/manifests/worldpop_sources.csv",
        "reference_year": REFERENCE_YEAR,
        "raster_crs": window["crs"],
        "pixel_size_deg": list(window["scale"]),
        "nodata": window["nodata"],
        "analysis_crs": ANALYSIS_CRS,
        "method": "격자 중심점이 못 기준 반경(유클리드) 안에 있는 셀의 인구 합계; 면적가중 아님",
        "pond_count": int(len(result)),
        "summary": {
            suffix: {
                "min": float(result[f"worldpop_population_{suffix}"].min()),
                "median": float(result[f"worldpop_population_{suffix}"].median()),
                "max": float(result[f"worldpop_population_{suffix}"].max()),
                "zero_population_ponds": int((result[f"worldpop_population_{suffix}"] == 0).sum()),
            }
            for suffix in RADII.values()
        },
        "use_policy": "참고·비교용. 국내 공식 인구격자(official_population_*)를 대체하지 않으며 제출문서의 공식 Buffer 인구로 표기하지 않는다.",
        "output": "data/analysis/worldpop_reference_buffer.csv",
    }
    write_json(ANALYSIS_DIR / "worldpop_reference_buffer.json", summary)
    return summary


if __name__ == "__main__":
    output = run()
    print(f"WorldPop 참고 Buffer: {output['status']}")

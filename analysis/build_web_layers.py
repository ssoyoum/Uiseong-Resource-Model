"""웹 지도 표시 전용 경량 GeoJSON을 만든다.

분석 입력 GeoJSON(agricultural_areas, uiseong_emd)은 그대로 두고, Leaflet 표시용 사본만
EPSG:5174에서 단순화한 뒤 좌표 소수점을 줄여 저장한다. 면적 등 속성값은 원본 값을 유지한다.
"""

from __future__ import annotations

import json

import shapely

try:
    from common import ANALYSIS_CRS, ANALYSIS_DIR, GEOJSON_DIR, load_geojson, write_json
except ImportError:
    from analysis.common import ANALYSIS_CRS, ANALYSIS_DIR, GEOJSON_DIR, load_geojson, write_json


SIMPLIFY_TOLERANCE_M = 5.0
COORDINATE_DECIMALS = 5  # 위경도 1e-5도 ≈ 1m
LAYERS = {
    "agricultural_areas.geojson": "agricultural_areas_web.geojson",
    "uiseong_emd.geojson": "uiseong_emd_web.geojson",
}


def round_coordinates(value):
    if isinstance(value, (int, float)):
        return round(value, COORDINATE_DECIMALS)
    return [round_coordinates(item) for item in value]


def build_layer(source_name: str, output_name: str) -> dict:
    source = GEOJSON_DIR / source_name
    layer = load_geojson(source, ANALYSIS_CRS)
    simplified = layer.copy()
    simplified["geometry"] = layer.geometry.simplify(SIMPLIFY_TOLERANCE_M, preserve_topology=True)
    web = simplified.to_crs("EPSG:4326")
    # set_precision은 격자에 맞추면서 유효한 geometry를 유지한다(단순 반올림은 자기교차를 만들 수 있음).
    snapped = shapely.set_precision(web.geometry.values, grid_size=10 ** -COORDINATE_DECIMALS)
    # 1m 격자보다 작은 Polygon은 비어 버리므로 단순화한 좌표를 그대로 둔다(피처 수 유지).
    collapsed = shapely.is_empty(snapped) | shapely.is_missing(snapped)
    web["geometry"] = [original if lost else geometry for original, geometry, lost in zip(web.geometry.values, snapped, collapsed)]
    payload = json.loads(web.to_json(drop_id=True))
    payload.pop("crs", None)
    for feature, lost in zip(payload["features"], collapsed):
        # 격자에 맞춘 값의 부동소수 꼬리(예: 128.28898000000001)만 정리한다.
        if not lost:
            feature["geometry"]["coordinates"] = round_coordinates(feature["geometry"]["coordinates"])
    output = GEOJSON_DIR / output_name
    output.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    original_area = float(layer.geometry.area.sum())
    simplified_area = float(simplified.geometry.area.sum())
    return {
        "source": f"data/geojson/{source_name}",
        "output": f"data/geojson/{output_name}",
        "feature_count": int(len(layer)),
        "kept_unsnapped_small_features": int(collapsed.sum()),
        "source_kb": round(source.stat().st_size / 1024, 1),
        "output_kb": round(output.stat().st_size / 1024, 1),
        "area_change_pct": round((simplified_area - original_area) / original_area * 100, 4) if original_area else None,
    }


def run() -> dict:
    layers = [build_layer(source, output) for source, output in LAYERS.items()]
    summary = {
        "status": "PASS",
        "purpose": "Leaflet 표시 전용. 분석은 원본 GeoJSON을 사용한다.",
        "simplify_tolerance_m": SIMPLIFY_TOLERANCE_M,
        "simplify_crs": ANALYSIS_CRS,
        "coordinate_decimals": COORDINATE_DECIMALS,
        "layers": layers,
    }
    write_json(ANALYSIS_DIR / "web_layers_summary.json", summary)
    return summary


if __name__ == "__main__":
    for item in run()["layers"]:
        print(f"{item['output']}: {item['source_kb']}KB -> {item['output_kb']}KB, 면적 변화 {item['area_change_pct']}%")

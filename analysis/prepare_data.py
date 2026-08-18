"""의성군 못 데이터를 분석용 CSV와 지도용 GeoJSON으로 변환한다."""

from pathlib import Path
import json

import geopandas as gpd
import numpy as np
import pandas as pd
from pyproj import Transformer
from shapely.geometry import Point, mapping


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "의성"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
GEOJSON_DIR = BASE_DIR / "data" / "geojson"
ANALYSIS_DIR = BASE_DIR / "data" / "analysis"

for directory in (PROCESSED_DIR, GEOJSON_DIR, ANALYSIS_DIR):
    directory.mkdir(parents=True, exist_ok=True)

# 원본 X/Y 좌표계. 기존 EPSG:5186은 이 자료에 맞지 않아 의성군 밖으로 변환됐다.
SOURCE_CRS = "EPSG:5174"
WGS84 = "EPSG:4326"


def find_source_files() -> tuple[Path, Path]:
    raw_path = next(DATA_DIR.glob("*_TM.add"))
    boundary_path = next(
        path for path in DATA_DIR.rglob("의성군.shp")
        if path.parent.name == "의성"
    )
    return raw_path, boundary_path


def nearest_neighbor_distance(xy: np.ndarray) -> dict[str, float]:
    distances = []
    for index, current in enumerate(xy):
        others = np.delete(xy, index, axis=0)
        if others.size:
            distances.append(float(np.min(np.linalg.norm(others - current, axis=1))))

    if not distances:
        return {"mean": 0.0, "median": 0.0, "min": 0.0, "max": 0.0}

    values = np.array(distances)
    return {
        "mean": float(values.mean()),
        "median": float(np.median(values)),
        "min": float(values.min()),
        "max": float(values.max()),
    }


def main() -> None:
    raw_path, boundary_path = find_source_files()
    boundary = gpd.read_file(boundary_path).to_crs(WGS84).geometry.iloc[0]

    df = pd.read_csv(raw_path, sep="\t", encoding="cp949", dtype=str)
    required = ["연번", "주소", "총저수량(천톤)", "X", "Y"]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(f"필수 컬럼이 없습니다: {missing}")

    df["총저수량(천톤)"] = pd.to_numeric(df["총저수량(천톤)"], errors="coerce")
    df["X"] = pd.to_numeric(df["X"], errors="coerce")
    df["Y"] = pd.to_numeric(df["Y"], errors="coerce")
    df = df.dropna(subset=["X", "Y", "총저수량(천톤)"]).copy()
    df["지역명"] = df["주소"].fillna("미상").map(lambda value: str(value).split()[0])

    transformer = Transformer.from_crs(SOURCE_CRS, WGS84, always_xy=True)
    transformed = [transformer.transform(x, y) for x, y in zip(df["X"], df["Y"])]
    points = gpd.GeoSeries(
        [Point(lon, lat) for lon, lat in transformed],
        crs=WGS84,
    )

    # 경계 밖 자료는 지도와 분석에서 모두 제외한다.
    inside = points.map(boundary.covers)
    df = df.loc[inside.to_numpy()].reset_index(drop=True)
    transformed = [point for point, keep in zip(transformed, inside) if keep]
    xy = df[["X", "Y"]].to_numpy(dtype=float)

    df.to_csv(PROCESSED_DIR / "ponds.csv", index=False, encoding="utf-8-sig")

    features = []
    for row, (lon, lat) in zip(df.to_dict("records"), transformed):
        features.append({
            "type": "Feature",
            "properties": {
                "id": str(row["연번"]),
                "address": row["주소"],
                "region": row["지역명"],
                "capacity": float(row["총저수량(천톤)"]),
                "source": "의성군 주소 자료",
                "management": "미기재",
                "lat": float(lat),
                "lng": float(lon),
            },
            "geometry": {"type": "Point", "coordinates": [float(lon), float(lat)]},
        })

    with (GEOJSON_DIR / "ponds.geojson").open("w", encoding="utf-8") as file:
        json.dump({"type": "FeatureCollection", "features": features}, file, ensure_ascii=False, separators=(",", ":"))

    simplified_boundary = boundary.simplify(0.00005, preserve_topology=True)
    boundary_geojson = {
        "type": "FeatureCollection",
        "bbox": list(simplified_boundary.bounds),
        "features": [{
            "type": "Feature",
            "properties": {"name": "의성군"},
            "geometry": mapping(simplified_boundary),
        }],
    }
    with (GEOJSON_DIR / "uiseong_boundary.geojson").open("w", encoding="utf-8") as file:
        json.dump(boundary_geojson, file, ensure_ascii=False, separators=(",", ":"))

    summary = (
        df.groupby("지역명", as_index=False)
        .agg(시설수=("주소", "count"), 총용량=("총저수량(천톤)", "sum"), 평균용량=("총저수량(천톤)", "mean"))
        .sort_values("총용량", ascending=False)
        .reset_index(drop=True)
    )
    summary.to_csv(ANALYSIS_DIR / "region_summary.csv", index=False, encoding="utf-8-sig")
    with (ANALYSIS_DIR / "region_summary.json").open("w", encoding="utf-8") as file:
        json.dump(summary.to_dict(orient="records"), file, ensure_ascii=False, indent=2)
    with (ANALYSIS_DIR / "distance_cluster_summary.json").open("w", encoding="utf-8") as file:
        json.dump(nearest_neighbor_distance(xy), file, ensure_ascii=False, indent=2)

    print(f"의성군 경계 안의 못 {len(df)}개를 저장했습니다.")
    print(f"경계 bounds: {[round(value, 6) for value in boundary.bounds]}")


if __name__ == "__main__":
    main()

"""포트폴리오용 추가 GIS 분석 A, B, C를 실행한다.

A. 시설 간 최소거리, 최근접 이웃비율, DBSCAN 군집(Research Note)
B. 저수량 가중 중심점과 상위 시설 위치, 읍면별·관리주체별 비교
C. 못 주변 농업지역 Buffer/Intersection과 용량 상관 검토

분석 결과는 웹 페이지가 바로 읽을 수 있는 JSON으로 저장한다.
"""

from pathlib import Path
import json

import geopandas as gpd
import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy.spatial.distance import cdist
from scipy.stats import pearsonr, spearmanr
from sklearn.cluster import DBSCAN
from shapely.geometry import Point, mapping


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "의성"
ANALYSIS_DIR = BASE_DIR / "data" / "analysis"
SOURCE_CRS = "EPSG:5174"
WGS84 = "EPSG:4326"
DBSCAN_EPS = 1500
DBSCAN_MIN_SAMPLES = 4
BUFFER_RADII = (500, 1000)


def find_file(pattern: str, predicate=None) -> Path:
    for path in DATA_DIR.rglob(pattern):
        if predicate is None or predicate(path):
            return path
    raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {pattern}")


def to_float(value):
    if pd.isna(value):
        return None
    return float(value)


def rounded(value, digits=3):
    if value is None or pd.isna(value):
        return None
    return round(float(value), digits)


def load_ponds_and_boundary():
    point_path = find_file("1.shp")
    boundary_path = find_file("*.shp", lambda path: path.parent.name == "의성" and path.name != "1.shp")

    points = gpd.read_file(point_path, encoding="cp949")
    # 1.shp에는 CRS가 기록되어 있지 않으므로 원본 X/Y의 좌표계를 명시한다.
    points = points.set_crs(SOURCE_CRS, allow_override=True)
    boundary = gpd.read_file(boundary_path).to_crs(WGS84).geometry.iloc[0]

    capacity_col = next(column for column in points.columns if str(column).startswith("총저수량"))
    points["capacity"] = pd.to_numeric(points[capacity_col], errors="coerce")
    points["address"] = points["주소"].fillna("미상").astype(str)
    points["region"] = points["address"].str.split().str[0]
    points["X"] = pd.to_numeric(points["X"], errors="coerce")
    points["Y"] = pd.to_numeric(points["Y"], errors="coerce")
    points = points.dropna(subset=["X", "Y", "capacity"]).copy()

    transformer = Transformer.from_crs(SOURCE_CRS, WGS84, always_xy=True)
    points["lng"], points["lat"] = zip(*[
        transformer.transform(x, y) for x, y in zip(points["X"], points["Y"])
    ])
    points["inside"] = [boundary.covers(Point(lng, lat)) for lng, lat in zip(points["lng"], points["lat"])]
    points = points.loc[points["inside"]].copy().reset_index(drop=True)
    points["id"] = points["연번"].astype(str)
    return points, boundary, point_path, boundary_path


def find_emd_file():
    return find_file("*.shp", lambda path: path.name == "의성군내_읍면동.shp")


def spatial_join_regions(points):
    """못 Point와 읍면동 Polygon을 GeoPandas spatial join으로 연결한다."""
    emd_path = find_emd_file()
    emd = gpd.read_file(emd_path).to_crs(SOURCE_CRS)
    region_column = next(column for column in emd.columns if str(column).endswith("KOR_NM"))
    emd = emd[[region_column, "geometry"]].rename(columns={region_column: "spatial_region"})

    joined = gpd.sjoin(
        points[["id", "geometry"]],
        emd,
        how="left",
        predicate="within",
    ).sort_index()
    points = points.copy()
    points["region"] = joined["spatial_region"].fillna(points["region"]).to_numpy()
    return points, emd, emd_path


def load_agricultural_areas(boundary):
    """농지·농업진흥지역 Polygon을 의성군 경계와 intersection 한다."""
    agri_path = next(
        path for path in DATA_DIR.rglob("*.shp")
        if path.stat().st_size == 33971980
    )
    agri = gpd.read_file(agri_path).to_crs(SOURCE_CRS)
    boundary_projected = gpd.GeoDataFrame(
        {"boundary": ["의성군"]},
        geometry=gpd.GeoSeries([boundary], crs=WGS84).to_crs(SOURCE_CRS),
        crs=SOURCE_CRS,
    )
    clipped = gpd.overlay(agri[["geometry"]], boundary_projected, how="intersection", keep_geom_type=False)
    clipped = clipped.loc[clipped.geometry.geom_type.isin(["Polygon", "MultiPolygon"])].copy()
    return clipped, agri_path


def agricultural_buffer_analysis(points, agricultural_areas):
    """못 주변 Buffer와 농업지역 Polygon의 Intersection 면적을 계산한다."""
    spatial_index = agricultural_areas.sindex
    records_by_radius = {}

    for radius in BUFFER_RADII:
        records = []
        union_buffer = None
        for _, row in points.iterrows():
            buffer = row.geometry.buffer(radius)
            union_buffer = buffer if union_buffer is None else union_buffer.union(buffer)
            candidates = agricultural_areas.iloc[
                list(spatial_index.query(buffer, predicate="intersects"))
            ]
            area = sum(
                polygon.intersection(buffer).area
                for polygon in candidates.geometry
                if not polygon.is_empty
            )
            records.append({
                "id": row["id"],
                "address": row["address"],
                "region": row["region"],
                "capacity": rounded(row["capacity"], 1),
                "agricultural_area_m2": rounded(area, 1),
                "agricultural_area_ha": rounded(area / 10000, 3),
                "agricultural_ratio": rounded((area / buffer.area) * 100, 2),
                "lat": rounded(row["lat"], 6),
                "lng": rounded(row["lng"], 6),
            })

        result = pd.DataFrame(records)
        pearson = pearsonr(result["capacity"], result["agricultural_area_m2"])
        spearman = spearmanr(result["capacity"], result["agricultural_area_m2"])
        correlation = float(spearman.statistic)
        if abs(correlation) < 0.3:
            interpretation = "상관관계가 약함"
        elif correlation > 0:
            interpretation = "용량이 클수록 주변 농업지역이 많은 양의 관계"
        else:
            interpretation = "용량이 클수록 주변 농업지역이 적은 음의 관계"

        records_by_radius[str(radius)] = {
            "radius_m": radius,
            "facility_count": len(result),
            "total_agricultural_area_m2": rounded(result["agricultural_area_m2"].sum(), 1),
            "mean_agricultural_area_m2": rounded(result["agricultural_area_m2"].mean(), 1),
            "median_agricultural_area_m2": rounded(result["agricultural_area_m2"].median(), 1),
            "mean_agricultural_ratio": rounded(result["agricultural_ratio"].mean(), 2),
            "union_agricultural_area_m2": rounded(agricultural_areas.geometry.intersection(union_buffer).area.sum(), 1),
            "pearson_r": rounded(pearson.statistic, 3),
            "pearson_p_value": rounded(pearson.pvalue, 4),
            "spearman_r": rounded(spearman.statistic, 3),
            "spearman_p_value": rounded(spearman.pvalue, 4),
            "correlation_interpretation": interpretation,
            "scatter": records,
        }
    return records_by_radius


def nearest_neighbor_analysis(points, boundary):
    unique_points = points.drop_duplicates(subset=["X", "Y"]).copy()
    coordinates = unique_points[["X", "Y"]].to_numpy(dtype=float)
    distances = cdist(coordinates, coordinates)
    np.fill_diagonal(distances, np.inf)
    nearest = distances.min(axis=1)

    area_m2 = float(gpd.GeoSeries([boundary], crs=WGS84).to_crs(SOURCE_CRS).area.iloc[0])
    count = len(coordinates)
    expected = 0.5 / np.sqrt(count / area_m2)
    observed = float(nearest.mean())
    ratio = observed / expected
    standard_error = 0.26136 * np.sqrt(area_m2 / count)
    z_score = (observed - expected) / standard_error if standard_error else 0.0

    if ratio < 0.8 and abs(z_score) < 1.96:
        interpretation = "약한 군집 경향(통계적 유의성 낮음)"
    elif ratio < 0.8:
        interpretation = "군집 경향"
    elif ratio > 1.2:
        interpretation = "규칙적·균등 분포 경향"
    else:
        interpretation = "무작위 분포에 가까움"

    labels = DBSCAN(
        eps=DBSCAN_EPS,
        min_samples=DBSCAN_MIN_SAMPLES,
        metric="euclidean",
    ).fit_predict(coordinates)
    cluster_ids = sorted(set(labels) - {-1})
    cluster_sizes = [int((labels == cluster_id).sum()) for cluster_id in cluster_ids]
    clusters = []
    for cluster_id in cluster_ids:
        cluster_points = unique_points.loc[labels == cluster_id]
        clusters.append({
            "cluster": int(cluster_id) + 1,
            "count": int(len(cluster_points)),
            "center_x": rounded(cluster_points["X"].mean(), 1),
            "center_y": rounded(cluster_points["Y"].mean(), 1),
        })

    histogram_edges = np.array([0, 250, 500, 750, 1000, 1500, 2000, 3000, 5000, np.inf])
    histogram_counts, _ = np.histogram(nearest, bins=histogram_edges)
    histogram = []
    for index, count_in_bin in enumerate(histogram_counts):
        start = int(histogram_edges[index])
        end = histogram_edges[index + 1]
        label = f"{start}–{int(end)}" if np.isfinite(end) else f"{start}+"
        histogram.append({"label": label, "count": int(count_in_bin)})

    return {
        "facility_count": int(len(points)),
        "unique_coordinate_count": int(len(unique_points)),
        "duplicate_coordinate_count": int(len(points) - len(unique_points)),
        "study_area_km2": rounded(area_m2 / 1_000_000, 2),
        "mean_nearest_distance_m": rounded(observed, 1),
        "median_nearest_distance_m": rounded(np.median(nearest), 1),
        "nearest_distance_min_m": rounded(nearest.min(), 1),
        "nearest_distance_max_m": rounded(nearest.max(), 1),
        "expected_nearest_distance_m": rounded(expected, 1),
        "nearest_neighbor_ratio": rounded(ratio, 3),
        "z_score": rounded(z_score, 3),
        "interpretation": interpretation,
        "dbscan": {
            "eps_m": DBSCAN_EPS,
            "min_samples": DBSCAN_MIN_SAMPLES,
            "cluster_count": len(cluster_ids),
            "noise_count": int((labels == -1).sum()),
            "largest_cluster_size": max(cluster_sizes, default=0),
            "clusters": clusters,
        },
        "histogram": histogram,
    }


def transform_point(transformer, x, y):
    lng, lat = transformer.transform(float(x), float(y))
    return {"x": rounded(x, 1), "y": rounded(y, 1), "lng": rounded(lng, 6), "lat": rounded(lat, 6)}


def weighted_centroid_analysis(points):
    transformer = Transformer.from_crs(SOURCE_CRS, WGS84, always_xy=True)

    def centroid(frame):
        weights = frame["capacity"].to_numpy(dtype=float)
        x = np.average(frame["X"], weights=weights)
        y = np.average(frame["Y"], weights=weights)
        return transform_point(transformer, x, y)

    unweighted = transform_point(transformer, points["X"].mean(), points["Y"].mean())
    weighted = centroid(points)
    top = points.nlargest(10, "capacity")
    top_centroid = centroid(top)

    top_facilities = []
    for _, row in top.iterrows():
        top_facilities.append({
            "id": row["id"],
            "address": row["address"],
            "region": row["region"],
            "capacity": rounded(row["capacity"], 1),
            "lat": rounded(row["lat"], 6),
            "lng": rounded(row["lng"], 6),
        })

    regional = []
    for region, frame in points.groupby("region"):
        item = centroid(frame)
        regional.append({
            "region": region,
            "facility_count": int(len(frame)),
            "total_capacity": rounded(frame["capacity"].sum(), 1),
            "weighted_lat": item["lat"],
            "weighted_lng": item["lng"],
        })
    regional.sort(key=lambda item: item["total_capacity"], reverse=True)

    return {
        "weighted_centroid": weighted,
        "unweighted_centroid": unweighted,
        "top_10_centroid": top_centroid,
        "top_facilities": top_facilities,
        "regional_weighted_centroids": regional,
    }


def read_management_workbook():
    workbook = find_file("*.xlsx", lambda path: path.stat().st_size == 48702)
    frames = []
    for sheet in pd.ExcelFile(workbook).sheet_names:
        raw = pd.read_excel(workbook, sheet_name=sheet, header=3)
        raw = raw.iloc[:, :7].copy()
        raw.columns = ["id", "name", "region", "village", "parcel", "capacity", "note"]
        raw["capacity"] = pd.to_numeric(raw["capacity"], errors="coerce")
        raw["region"] = raw["region"].astype("string").str.strip()
        raw = raw.dropna(subset=["region", "capacity"])
        raw["management"] = "의성군 관리" if sheet == "의성군" else "한국농어촌공사 관리"
        frames.append(raw)
    return pd.concat(frames, ignore_index=True), workbook


def regional_analysis(points, emd=None):
    area_by_region = {}
    if emd is not None:
        area_by_region = (
            emd.assign(area_km2=emd.geometry.area / 1_000_000)
            .groupby("spatial_region")["area_km2"]
            .sum()
            .to_dict()
        )
    records = []
    for region, frame in points.groupby("region"):
        capacities = frame["capacity"].to_numpy(dtype=float)
        area_km2 = float(area_by_region.get(region, 0))
        records.append({
            "region": region,
            "facility_count": int(len(frame)),
            "total_capacity": rounded(capacities.sum(), 1),
            "mean_capacity": rounded(capacities.mean(), 1),
            "median_capacity": rounded(np.median(capacities), 1),
            "min_capacity": rounded(capacities.min(), 1),
            "max_capacity": rounded(capacities.max(), 1),
            "q1": rounded(np.percentile(capacities, 25), 1),
            "q3": rounded(np.percentile(capacities, 75), 1),
            "area_km2": rounded(area_km2, 2),
            "facilities_per_km2": rounded(len(frame) / area_km2, 3) if area_km2 else 0,
        })
    records.sort(key=lambda item: item["total_capacity"], reverse=True)
    return records


def management_analysis(workbook_data):
    records = []
    for management, frame in workbook_data.groupby("management"):
        records.append({
            "management": management,
            "facility_count": int(len(frame)),
            "total_capacity": rounded(frame["capacity"].sum(), 1),
            "mean_capacity": rounded(frame["capacity"].mean(), 1),
        })
    records.sort(key=lambda item: item["total_capacity"], reverse=True)
    return records


def main():
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    points, boundary, point_path, boundary_path = load_ponds_and_boundary()
    points, emd, emd_path = spatial_join_regions(points)
    agricultural_areas, agricultural_path = load_agricultural_areas(boundary)
    workbook_data, workbook_path = read_management_workbook()

    # Leaflet에서 사용할 농업진흥지역 Polygon은 WGS84 GeoJSON으로 저장한다.
    agricultural_web = agricultural_areas.copy()
    agricultural_web["geometry"] = agricultural_web.geometry.simplify(2, preserve_topology=True)
    agricultural_geojson = agricultural_web.to_crs(WGS84).copy()
    agricultural_geojson["area_ha"] = agricultural_areas.to_crs(SOURCE_CRS).area / 10000
    agricultural_geojson["area_ha"] = agricultural_geojson["area_ha"].round(3)
    agricultural_geojson.to_file(
        BASE_DIR / "data" / "geojson" / "agricultural_areas.geojson",
        driver="GeoJSON",
        encoding="utf-8",
    )

    # E 결과를 읍면동 Polygon 속성에 넣어 Leaflet choropleth 레이어로 저장한다.
    region_area = emd.assign(area_km2=emd.geometry.area / 1_000_000).groupby("spatial_region")["area_km2"].sum().to_dict()
    region_totals = points.groupby("region").agg(
        facility_count=("id", "count"),
        total_capacity=("capacity", "sum"),
    ).to_dict("index")
    emd_web = emd.to_crs(WGS84).copy()
    emd_web["facility_count"] = emd_web["spatial_region"].map(
        lambda region: region_totals.get(region, {}).get("facility_count", 0)
    )
    emd_web["total_capacity"] = emd_web["spatial_region"].map(
        lambda region: round(region_totals.get(region, {}).get("total_capacity", 0), 1)
    )
    emd_web["area_km2"] = emd_web["spatial_region"].map(lambda region: round(region_area.get(region, 0), 2))
    emd_web["facilities_per_km2"] = emd_web.apply(
        lambda row: round(row["facility_count"] / row["area_km2"], 3) if row["area_km2"] else 0,
        axis=1,
    )
    emd_web[["spatial_region", "facility_count", "total_capacity", "area_km2", "facilities_per_km2", "geometry"]].to_file(
        BASE_DIR / "data" / "geojson" / "uiseong_emd.geojson",
        driver="GeoJSON",
        encoding="utf-8",
    )

    result = {
        "meta": {
            "point_source": str(point_path.relative_to(BASE_DIR)),
            "boundary_source": str(boundary_path.relative_to(BASE_DIR)),
            "emd_source": str(emd_path.relative_to(BASE_DIR)),
            "agricultural_source": str(agricultural_path.relative_to(BASE_DIR)),
            "workbook_source": str(workbook_path.relative_to(BASE_DIR)),
            "source_crs": SOURCE_CRS,
            "analysis_scope": "의성군 행정경계 내부 자료",
        },
        "c": nearest_neighbor_analysis(points, boundary),
        "d": weighted_centroid_analysis(points),
        "e": {
            "join_method": "GeoPandas spatial join (Point within 읍면동 Polygon)",
            "spatial_join_match_count": int(points["region"].notna().sum()),
            "csv_region_summary": regional_analysis(points, emd),
            "xlsx_management_summary": management_analysis(workbook_data),
            "xlsx_record_count": int(len(workbook_data)),
        },
        "agriculture": {
            "source_type": "농지·농업진흥지역 Polygon",
            "polygon_count": int(len(agricultural_areas)),
            "total_area_ha": rounded(agricultural_areas.geometry.area.sum() / 10000, 2),
            "buffers": agricultural_buffer_analysis(points, agricultural_areas),
        },
    }
    output_path = ANALYSIS_DIR / "advanced_analysis.json"
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(result, file, ensure_ascii=False, indent=2)

    print(f"분석 결과 저장: {output_path}")
    print(f"C 최근접 이웃비율: {result['c']['nearest_neighbor_ratio']} ({result['c']['interpretation']})")
    print(f"C DBSCAN 군집: {result['c']['dbscan']['cluster_count']}개")
    print(f"D 전체 가중 중심: {result['d']['weighted_centroid']['lat']}, {result['d']['weighted_centroid']['lng']}")
    print(f"E 지역 집계: {len(result['e']['csv_region_summary'])}개 읍면")
    print(f"E XLSX 집계: {result['e']['xlsx_record_count']}개 시설")
    print(f"농업진흥지역: {result['agriculture']['polygon_count']}개 Polygon, {result['agriculture']['total_area_ha']}ha")
    for radius, item in result["agriculture"]["buffers"].items():
        print(f"  {radius}m 평균 농업지역: {item['mean_agricultural_area_m2']}m², Spearman={item['spearman_r']}")


if __name__ == "__main__":
    main()

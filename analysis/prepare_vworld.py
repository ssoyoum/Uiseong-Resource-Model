"""Prepare the VWorld source package for the Uiseong competition analysis.

The source package is kept in the repository's root ``vworld`` folder. Only
layers that actually intersect Uiseong are promoted to processed analysis data.
"""

from __future__ import annotations

import csv
import os
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

import geopandas as gpd
import pandas as pd

try:
    from common import (
        ANALYSIS_CRS,
        BASE_DIR,
        DATA_DIR,
        DATA_NOT_AVAILABLE,
        GEOJSON_DIR,
        MANIFEST_DIR,
        PROCESSED_DIR,
        RAW_DIR,
        ensure_output_dirs,
        load_geojson,
        write_json,
    )
except ImportError:
    from analysis.common import (
        ANALYSIS_CRS,
        BASE_DIR,
        DATA_DIR,
        DATA_NOT_AVAILABLE,
        GEOJSON_DIR,
        MANIFEST_DIR,
        PROCESSED_DIR,
        RAW_DIR,
        ensure_output_dirs,
        load_geojson,
        write_json,
    )


MANIFEST_COLUMNS = [
    "dataset_name",
    "provider",
    "vworld_layer_or_api",
    "accessed_at",
    "source_crs",
    "purpose",
    "processing",
    "license_conditions",
    "status",
    "source_path",
]

ROOT_VWORLD_SOURCE_DIR = BASE_DIR / "vworld"


def source_dir() -> Path:
    """Use the repository's existing root VWorld source package."""
    if ROOT_VWORLD_SOURCE_DIR.exists() and any(ROOT_VWORLD_SOURCE_DIR.iterdir()):
        return ROOT_VWORLD_SOURCE_DIR
    local = RAW_DIR / "vworld"
    if local.exists() and any(local.iterdir()):
        return local
    return local


def source_path_label(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return path.relative_to(BASE_DIR).as_posix()
    except ValueError:
        return Path(os.path.relpath(path, BASE_DIR)).as_posix()


def find_first(directory: Path, pattern: str) -> Path | None:
    matches = sorted(directory.glob(pattern)) if directory.exists() else []
    return matches[0] if matches else None


def find_boundary() -> gpd.GeoDataFrame:
    path = GEOJSON_DIR / "uiseong_boundary.geojson"
    if not path.exists():
        raise FileNotFoundError(f"의성군 경계를 찾을 수 없습니다: {path}")
    return load_geojson(path, ANALYSIS_CRS)


def read_zipped_layer(path: Path) -> gpd.GeoDataFrame:
    """Read the first shapefile in a VWorld ZIP without permanently extracting it."""
    with tempfile.TemporaryDirectory(prefix="uiseong_vworld_") as temp_dir:
        with zipfile.ZipFile(path) as archive:
            archive.extractall(temp_dir)
        shapefiles = sorted(Path(temp_dir).rglob("*.shp"))
        if not shapefiles:
            raise ValueError(f"ZIP 안에 SHP가 없습니다: {path.name}")
        return gpd.read_file(shapefiles[0], encoding="cp949")


def clip_to_uiseong(frame: gpd.GeoDataFrame, boundary: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if frame.crs is None:
        raise ValueError("원자료 CRS가 없어 VWorld 레이어를 사용할 수 없습니다.")
    frame = frame.to_crs(ANALYSIS_CRS)
    frame = frame.loc[frame.geometry.notna() & ~frame.geometry.is_empty].copy()
    boundary_geometry = boundary.geometry.union_all() if hasattr(boundary.geometry, "union_all") else boundary.geometry.unary_union
    if "COL_ADM_SE" in frame.columns:
        code_mask = frame["COL_ADM_SE"].astype(str).str.strip().eq("47730")
        frame = frame.loc[code_mask].copy()
    else:
        frame = frame.loc[frame.intersects(boundary_geometry)].copy()
    if frame.empty:
        return frame
    frame["geometry"] = frame.geometry.intersection(boundary_geometry)
    return frame.loc[frame.geometry.notna() & ~frame.geometry.is_empty].copy()


def text_value(row, *columns: str) -> str:
    for column in columns:
        if column not in row:
            continue
        value = row[column]
        if value is None:
            continue
        value = str(value).strip()
        if value and value.lower() not in {"none", "nan"}:
            return value
    return ""


def classify_facility(row) -> str:
    text = " ".join(text_value(row, "ALIAS", "REMARK", "MNUM").split()).lower()
    if any(word in text for word in ("관광", "온천", "골프", "관광지")):
        return "tourism"
    if any(word in text for word in ("박물관", "문화원", "문학관", "도서관", "미술관", "문화")):
        return "culture"
    if any(word in text for word in ("학교", "교육", "대학", "수련")):
        return "education"
    if any(word in text for word in ("병원", "보건", "의료", "약국")):
        return "health"
    if any(word in text for word in ("경찰", "소방", "119", "공공청사", "군청", "사무소", "행정")):
        return "public_safety"
    if any(word in text for word in ("체육", "운동")):
        return "sports"
    return "public_facility"


def normalize_facilities(frame: gpd.GeoDataFrame, source_layer: str, source_file: Path) -> gpd.GeoDataFrame:
    result = gpd.GeoDataFrame(frame.copy(), geometry="geometry", crs=ANALYSIS_CRS)
    result["source_layer"] = source_layer
    result["source_file"] = source_file.name
    result["facility_name"] = result.apply(lambda row: text_value(row, "ALIAS", "REMARK", "MNUM"), axis=1)
    result["facility_category"] = result.apply(classify_facility, axis=1)
    result["admin_code"] = result.get("COL_ADM_SE", "47730")
    result["provider"] = "VWorld"
    columns = [
        "facility_name",
        "facility_category",
        "source_layer",
        "source_file",
        "admin_code",
        "provider",
        "geometry",
    ]
    return result[columns]


def inventory_records(directory: Path) -> list[dict[str, object]]:
    records = []
    for path in sorted(directory.iterdir()) if directory.exists() else []:
        name = path.name
        if name in {"gb_r032.zip", "gb_r033.zip"}:
            classification = "생활SOC 2020 입지·수요분석 자료; 현재 파일 범위가 의성군 밖"
            action = "아이디어로 보류; 의성군 포함 버전 확보 전 사용하지 않음"
            status = "OUT_OF_SCOPE_NO_UISEONG_COVERAGE"
        elif name.startswith("LSMD_CONT_UO000"):
            classification = "도시계획 관련 Polygon; 의성군 feature 없음"
            action = "현재 분석에서 제외"
            status = "NO_UISEONG_FEATURES"
        elif name.startswith("LSMD_CONT_UO601"):
            classification = "관광지·관광특구 관련 Polygon"
            action = "의성군 feature를 시설·관광 context로 처리"
            status = "USED"
        elif name.startswith("LSMD_CONT_UQ164"):
            classification = "도시계획시설 관련 Polygon; 공공·교육·문화·안전시설 속성 포함"
            action = "의성군 feature를 생활·공공시설로 처리"
            status = "USED"
        elif name == "Z_UPIS_C_UQ151.xlsx":
            classification = "도시계획도로 테이블 정의서"
            action = "실제 도로 SHP 확보 전까지 정의서로만 보관"
            status = "SCHEMA_ONLY_ROAD_NOT_AVAILABLE"
        elif name.startswith("T_W_BASE_"):
            classification = "교통·문화지수 비공간 통계 테이블"
            action = "의성군 시군구 배경지표로 별도 처리"
            status = "CONTEXT_ONLY"
        elif name == "OA_IN.zip":
            classification = "읍·면·격자형 통계 TXT 묶음"
            action = "기존 행정안전부 인구자료와 비교 후 필요 시 보조 사용"
            status = "PUBLIC_STATISTICS_REFERENCE"
        elif name.lower().endswith((".hwp", ".xls", ".xlsx")):
            classification = "정의서·제출서류·참조코드 문서"
            action = "분석 원자료가 아닌 메타데이터·제출 참고자료로 보관"
            status = "METADATA_OR_DOCUMENT"
        else:
            classification = "미분류 파일"
            action = "내용 확인 후 분류 필요"
            status = "REVIEW_REQUIRED"
        records.append({
            "file_name": name,
            "file_type": "directory" if path.is_dir() else path.suffix.lower().lstrip("."),
            "size_bytes": path.stat().st_size if path.is_file() else None,
            "classification": classification,
            "recommended_action": action,
            "status": status,
            "source_path": source_path_label(path),
        })
    return records


def prepare() -> dict:
    ensure_output_dirs()
    boundary = find_boundary()
    directory = source_dir()
    records: list[dict[str, str]] = []
    facilities: list[gpd.GeoDataFrame] = []

    source_specs = [
        ("LSMD_CONT_UQ164*.zip", "UQ164", "공공·생활·문화·교육시설", "못 주변 VWorld 생활시설 수"),
        ("LSMD_CONT_UO601*.zip", "UO601", "관광지·관광특구", "못 주변 VWorld 관광시설 수"),
    ]

    for pattern, layer, purpose_name, purpose in source_specs:
        source = find_first(directory, pattern)
        if source is None:
            records.append({
                "dataset_name": purpose_name,
                "provider": "VWorld",
                "vworld_layer_or_api": layer,
                "accessed_at": "",
                "source_crs": "",
                "purpose": purpose,
                "processing": "원자료를 찾지 못해 산출하지 않음",
                "license_conditions": "원자료 확보 후 사용조건 기록 필요",
                "status": DATA_NOT_AVAILABLE,
                "source_path": "",
            })
            continue
        layer_data = read_zipped_layer(source)
        source_crs = layer_data.crs.to_string() if layer_data.crs else ""
        clipped = clip_to_uiseong(layer_data, boundary)
        if not clipped.empty:
            facilities.append(normalize_facilities(clipped, layer, source))
        records.append({
            "dataset_name": purpose_name,
            "provider": "VWorld",
            "vworld_layer_or_api": layer,
            "accessed_at": "",
            "source_crs": source_crs,
            "purpose": purpose,
            "processing": f"의성군 코드 47730 및 경계로 선별·Clip; {ANALYSIS_CRS} 저장",
            "license_conditions": "VWorld 원자료 이용조건·출처표시·재배포 조건 확인 필요",
            "status": "AVAILABLE" if not clipped.empty else "NO_UISEONG_FEATURES",
            "source_path": source_path_label(source),
        })

    output_path = PROCESSED_DIR / "facilities" / "uiseong_facilities.gpkg"
    if facilities:
        combined = gpd.GeoDataFrame(pd.concat(facilities, ignore_index=True), geometry="geometry", crs=ANALYSIS_CRS)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        combined.to_file(output_path, layer="facilities", driver="GPKG")
        facility_count = len(combined)
    else:
        facility_count = 0

    records.append({
        "dataset_name": "의성군 도로",
        "provider": "VWorld",
        "vworld_layer_or_api": "UQ151",
        "accessed_at": "",
        "source_crs": "",
        "purpose": "못-도로 최근접거리",
        "processing": "Z_UPIS_C_UQ151.xlsx 정의서만 확인; 실제 도로 공간파일 없음",
        "license_conditions": "실제 도로 SHP 확보 후 사용조건 기록 필요",
        "status": DATA_NOT_AVAILABLE,
        "source_path": source_path_label(find_first(directory, "Z_UPIS_C_UQ151.xlsx")),
    })
    records.extend([
        {
            "dataset_name": "의성군 행정경계",
            "provider": "기존 프로젝트 자료",
            "vworld_layer_or_api": "",
            "accessed_at": "",
            "source_crs": ANALYSIS_CRS,
            "purpose": "분석 범위·공간검증",
            "processing": "기존 프로젝트 GeoJSON 사용; VWorld 출처로 추정하지 않음",
            "license_conditions": "기존 원자료 출처 확인 필요",
            "status": "EXISTING_LOCAL_DATA_NOT_VERIFIED",
            "source_path": source_path_label(GEOJSON_DIR / "uiseong_boundary.geojson"),
        },
        {
            "dataset_name": "농업지역",
            "provider": "기존 프로젝트 자료",
            "vworld_layer_or_api": "",
            "accessed_at": "",
            "source_crs": ANALYSIS_CRS,
            "purpose": "못 주변 농업지역 intersection",
            "processing": "기존 프로젝트 GeoJSON 사용; VWorld 출처로 추정하지 않음",
            "license_conditions": "기존 원자료 출처 확인 필요",
            "status": "EXISTING_LOCAL_DATA_NOT_VERIFIED",
            "source_path": source_path_label(GEOJSON_DIR / "agricultural_areas.geojson"),
        },
    ])

    manifest = MANIFEST_DIR / "vworld_sources.csv"
    with manifest.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=MANIFEST_COLUMNS)
        writer.writeheader()
        writer.writerows(records)

    inventory = inventory_records(directory)
    write_json(DATA_DIR / "analysis" / "vworld_layer_inventory.json", {
        "source_directory": source_path_label(directory),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "records": inventory,
    })
    used_layers = [record["dataset_name"] for record in records if record["status"] == "AVAILABLE"]
    write_json(DATA_DIR / "analysis" / "vworld_input_status.json", {
        "status": "AVAILABLE_PARTIAL" if used_layers else DATA_NOT_AVAILABLE,
        "source_directory": source_path_label(directory),
        "available_layers": used_layers,
        "facility_count": facility_count,
        "roads_status": DATA_NOT_AVAILABLE,
        "facilities_status": "AVAILABLE" if facility_count else DATA_NOT_AVAILABLE,
        "message": "VWorld UQ164·UO601의 의성군 범위만 처리했습니다. 도로는 실제 UQ151 공간파일이 없어 미산출입니다.",
    })
    return {
        "source_directory": directory,
        "records": records,
        "roads": False,
        "facilities": facility_count > 0,
        "facility_count": facility_count,
    }


def main() -> None:
    result = prepare()
    print(
        f"VWorld 입력: 도로={result['roads']}, "
        f"시설={result['facilities']} ({result['facility_count']}개), "
        f"source={source_path_label(result['source_directory'])}"
    )


if __name__ == "__main__":
    main()

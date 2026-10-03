"""데이터별 manifest를 AGENTS.md 4.2의 표준 12개 필드로 통합한다.

원본 manifest(vworld·population·sgis·traffic_culture·worldpop)를 단일 기준으로 읽고,
기록되지 않은 값은 추정하지 않고 DATA_NOT_AVAILABLE로 남긴다.
"""

from __future__ import annotations

import csv
import re
import subprocess
import zipfile
from pathlib import Path

try:
    from common import ANALYSIS_DIR, BASE_DIR, DATA_NOT_AVAILABLE, MANIFEST_DIR, read_json, write_json
except ImportError:
    from analysis.common import ANALYSIS_DIR, BASE_DIR, DATA_NOT_AVAILABLE, MANIFEST_DIR, read_json, write_json


STANDARD_COLUMNS = [
    "dataset_name",
    "provider",
    "layer_id",
    "reference_year",
    "download_url",
    "accessed_at",
    "crs",
    "license_url",
    "local_source_path",
    "processed_output",
    "usage_note",
    "redistribution_status",
]
EXTRA_COLUMNS = ["source_manifest", "source_status", "local_source_status", "raw_file_date"]
OUTPUT_PATH = MANIFEST_DIR / "source_manifest.csv"
NOT_SPATIAL = "NOT_SPATIAL_TABLE"

VWORLD_OUTPUTS = {
    "UQ164": "data/processed/facilities/uiseong_facilities.gpkg",
    "UO601": "data/processed/facilities/uiseong_facilities.gpkg",
    "UQ151": "data/processed/roads/uiseong_roads.gpkg",
}
SGIS_OUTPUTS = {
    "SGIS 지역통계 API": "data/analysis/sgis_indicator_availability.json",
    "SGIS 생활권역 주행인구": "data/processed/population/sgis_drive_population.csv",
}


def read_rows(name: str) -> list[dict]:
    path = MANIFEST_DIR / name
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def value(text: str | None) -> str:
    text = (text or "").strip()
    return text if text else DATA_NOT_AVAILABLE


def rel(path: str) -> str:
    return path.replace("\\", "/").strip()


def is_git_ignored(path: str) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "-q", path],
        cwd=BASE_DIR,
        capture_output=True,
    )
    return result.returncode == 0


def local_status(path: str) -> str:
    if not path or path == DATA_NOT_AVAILABLE:
        return DATA_NOT_AVAILABLE
    return "PRESENT" if (BASE_DIR / path).exists() else "MISSING_LOCAL"


def redistribution(path: str, license_url: str) -> str:
    raw = "RAW_NOT_REDISTRIBUTED" if is_git_ignored(path) else "RAW_IN_REPOSITORY"
    licence = "LICENSE_URL_RECORDED" if license_url != DATA_NOT_AVAILABLE else "LICENSE_UNVERIFIED"
    return f"{raw}; {licence}"


def zip_members(path: str) -> list[zipfile.ZipInfo]:
    full = BASE_DIR / path
    if full.suffix.lower() != ".zip" or not full.exists():
        return []
    with zipfile.ZipFile(full) as archive:
        return archive.infolist()


def zip_data_version(path: str) -> str:
    """VWorld LSMD 파일명 끝의 YYYYMM 데이터 버전(예: ..._47_202608.shp)."""
    for member in zip_members(path):
        match = re.search(r"_(\d{6})\.(shp|dbf)$", member.filename)
        if match:
            return match.group(1)
    return DATA_NOT_AVAILABLE


def zip_raw_file_date(path: str) -> str:
    """압축 내부 주 데이터파일의 수정일. 기준연도가 아니라 파일 작성일로만 사용한다."""
    for member in zip_members(path):
        if member.filename.lower().endswith((".shp", ".txt")):
            year, month, day = member.date_time[:3]
            return f"{year:04d}-{month:02d}-{day:02d}"
    return DATA_NOT_AVAILABLE


def traffic_years() -> dict[str, str]:
    context = read_json(ANALYSIS_DIR / "traffic_culture_context.json", {}) or {}
    years = {}
    for dataset in context.get("datasets", []):
        values = sorted(dataset.get("years") or [])
        if values:
            years[rel(dataset.get("source_path", ""))] = f"{values[0]}-{values[-1]}"
    return years


def vworld_rows() -> list[dict]:
    rows = []
    for row in read_rows("vworld_sources.csv"):
        layer = value(row.get("vworld_layer_or_api"))
        source_path = rel(row.get("source_path", ""))
        version = zip_data_version(source_path)
        rows.append({
            "dataset_name": row["dataset_name"],
            "provider": value(row.get("provider")),
            "layer_id": layer,
            "reference_year": version[:4] if version != DATA_NOT_AVAILABLE else DATA_NOT_AVAILABLE,
            "download_url": DATA_NOT_AVAILABLE,
            "accessed_at": value(row.get("accessed_at")),
            "crs": value(row.get("source_crs")),
            "license_url": DATA_NOT_AVAILABLE,
            "local_source_path": source_path,
            "processed_output": VWORLD_OUTPUTS.get(layer, source_path),
            "usage_note": "; ".join(filter(None, [
                row.get("purpose", ""),
                row.get("processing", ""),
                f"파일명 데이터버전 {version}" if version != DATA_NOT_AVAILABLE else "",
            ])),
            "license_note": row.get("license_conditions", ""),
            "source_manifest": "data/manifests/vworld_sources.csv",
            "source_status": value(row.get("status")),
        })
    return rows


def population_rows() -> list[dict]:
    rows = []
    for row in read_rows("population_sources.csv"):
        period = value(row.get("reference_period"))
        local_path = f"data/raw/population/mois_age_{period[:4]}_1year.csv" if period[:4].isdigit() else DATA_NOT_AVAILABLE
        rows.append({
            "dataset_name": f"{row['dataset_name']} ({period})",
            "provider": value(row.get("provider")),
            "layer_id": DATA_NOT_AVAILABLE,
            "reference_year": period[:4] if period[:4].isdigit() else period,
            "download_url": value(row.get("source_url")),
            "accessed_at": value(row.get("downloaded_at")),
            "crs": NOT_SPATIAL,
            "license_url": DATA_NOT_AVAILABLE,
            "local_source_path": local_path,
            "processed_output": "data/processed/population/uiseong_population.csv",
            "usage_note": f"기준월 {period}; {row.get('geographic_filter', '')}; {row.get('age_definition', '')}",
            "license_note": row.get("license_or_note", ""),
            "source_manifest": "data/manifests/population_sources.csv",
            "source_status": value(row.get("status")),
        })
    return rows


def sgis_rows() -> list[dict]:
    rows = []
    for row in read_rows("sgis_sources.csv"):
        name = row["dataset_name"]
        rows.append({
            "dataset_name": name,
            "provider": value(row.get("provider")),
            "layer_id": value(row.get("endpoint_or_method")),
            "reference_year": value(row.get("reference_period")),
            "download_url": value(row.get("source_url")),
            "accessed_at": DATA_NOT_AVAILABLE,
            "crs": "EPSG:5179 (API 요청 좌표)" if "생활권역" in name else NOT_SPATIAL,
            "license_url": DATA_NOT_AVAILABLE,
            "local_source_path": "API_RESPONSE",
            "processed_output": SGIS_OUTPUTS.get(name, DATA_NOT_AVAILABLE),
            "usage_note": f"{row.get('fields_or_use', '')}; {row.get('missing_value_rule', '')}",
            "license_note": "",
            "source_manifest": "data/manifests/sgis_sources.csv",
            "source_status": value(row.get("status")),
        })
    return rows


def traffic_rows() -> list[dict]:
    rows = []
    years = traffic_years()
    for row in read_rows("traffic_culture_sources.csv"):
        source_path = rel(row.get("source_table", ""))
        rows.append({
            "dataset_name": row["dataset_name"],
            "provider": DATA_NOT_AVAILABLE,
            "layer_id": Path(source_path).stem if source_path else DATA_NOT_AVAILABLE,
            "reference_year": years.get(source_path, DATA_NOT_AVAILABLE),
            "download_url": DATA_NOT_AVAILABLE,
            "accessed_at": DATA_NOT_AVAILABLE,
            "crs": NOT_SPATIAL,
            "license_url": DATA_NOT_AVAILABLE,
            "local_source_path": source_path,
            "processed_output": "data/analysis/traffic_culture_context.json",
            "usage_note": f"{row.get('analysis_role', '')}; 시군구 코드 {row.get('municipality_code', '')}; 시설별 접근성으로 복제하지 않음",
            "license_note": row.get("license_note", ""),
            "source_manifest": "data/manifests/traffic_culture_sources.csv",
            "source_status": value(row.get("status")),
        })
    return rows


def worldpop_rows() -> list[dict]:
    rows = []
    for row in read_rows("worldpop_sources.csv"):
        rows.append({
            "dataset_name": row["dataset_name"],
            "provider": value(row.get("provider")),
            "layer_id": DATA_NOT_AVAILABLE,
            "reference_year": value(row.get("reference_period")),
            "download_url": value(row.get("source_url")),
            "accessed_at": value(row.get("accessed_at")),
            "crs": DATA_NOT_AVAILABLE,
            "license_url": value(row.get("license_url")),
            "local_source_path": rel(row.get("local_path", "")),
            "processed_output": "data/analysis/worldpop_reference_buffer.csv",
            "usage_note": f"참고자료 전용; worldpop_population_500m·1km 별도 필드; 국내 공식 인구격자를 대체하지 않음; {row.get('note', '')}",
            "license_note": "",
            "source_manifest": "data/manifests/worldpop_sources.csv",
            "source_status": value(row.get("status")),
        })
    return rows


def run() -> dict:
    records = vworld_rows() + population_rows() + sgis_rows() + traffic_rows() + worldpop_rows()
    for record in records:
        path = record["local_source_path"]
        record["local_source_status"] = "API_RESPONSE" if path == "API_RESPONSE" else local_status(path)
        record["raw_file_date"] = zip_raw_file_date(path)
        if path == "API_RESPONSE":
            record["redistribution_status"] = "API_TERMS_UNVERIFIED"
        else:
            record["redistribution_status"] = redistribution(path, record["license_url"])
        if "확인 필요" in record.pop("license_note", ""):
            record["redistribution_status"] += "; 원본 manifest: 이용조건 확인 필요"

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=STANDARD_COLUMNS + EXTRA_COLUMNS)
        writer.writeheader()
        writer.writerows(records)

    missing_fields = {
        column: sum(record[column] == DATA_NOT_AVAILABLE for record in records)
        for column in STANDARD_COLUMNS
    }
    blank_cells = sum(not str(record.get(column, "")).strip() for record in records for column in STANDARD_COLUMNS)
    missing_local = [record["local_source_path"] for record in records if record["local_source_status"] == "MISSING_LOCAL"]
    checks = [
        {"name": "standard_fields_filled", "status": "PASS" if records and blank_cells == 0 else "FAIL", "details": {"blank_cells": blank_cells}},
        # 원자료는 Git 추적 제외 대상이므로 로컬 누락은 WARN으로만 기록한다.
        {"name": "local_sources_present", "status": "PASS" if not missing_local else "WARN", "details": {"missing_local": missing_local}},
    ]
    summary = {
        "status": "FAIL" if any(item["status"] == "FAIL" for item in checks) else "PASS",
        "checks": checks,
        "output": "data/manifests/source_manifest.csv",
        "record_count": len(records),
        "standard_columns": STANDARD_COLUMNS,
        "data_not_available_by_field": missing_fields,
        "note": "DATA_NOT_AVAILABLE는 원본 manifest에 기록되지 않은 값이며 추정으로 채우지 않았다.",
    }
    write_json(ANALYSIS_DIR / "source_manifest_summary.json", summary)
    return summary


if __name__ == "__main__":
    result = run()
    print(f"source manifest: {result['status']} ({result['record_count']}건)")

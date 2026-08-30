"""공모전 분석 모듈이 공유하는 경로·입력·출력 유틸리티."""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
GEOJSON_DIR = DATA_DIR / "geojson"
ANALYSIS_DIR = DATA_DIR / "analysis"
COMPETITION_DIR = ANALYSIS_DIR / "competition"
FIGURES_DIR = BASE_DIR / "analysis" / "figures"
MANIFEST_DIR = DATA_DIR / "manifests"

WGS84 = "EPSG:4326"
ANALYSIS_CRS = "EPSG:5174"
DATA_NOT_AVAILABLE = "DATA_NOT_AVAILABLE"


def ensure_output_dirs() -> None:
    for path in (
        RAW_DIR / "population",
        RAW_DIR / "facilities",
        RAW_DIR / "business",
        PROCESSED_DIR / "population",
        PROCESSED_DIR / "roads",
        PROCESSED_DIR / "facilities",
        GEOJSON_DIR,
        ANALYSIS_DIR,
        COMPETITION_DIR,
        FIGURES_DIR,
        MANIFEST_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)


def read_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8",
    )


def load_geojson(path: Path, target_crs: str | None = None) -> gpd.GeoDataFrame:
    frame = gpd.read_file(path)
    if frame.crs is None:
        frame = frame.set_crs(WGS84, allow_override=True)
    if target_crs:
        frame = frame.to_crs(target_crs)
    return frame


def load_ponds(target_crs: str | None = None) -> gpd.GeoDataFrame:
    path = GEOJSON_DIR / "ponds.geojson"
    if not path.exists():
        raise FileNotFoundError(f"시설 GeoJSON을 찾을 수 없습니다: {path}")
    ponds = load_geojson(path, target_crs)
    ponds["id"] = ponds["id"].astype(str)
    ponds["capacity"] = pd.to_numeric(ponds["capacity"], errors="coerce")
    return ponds


def find_data_file(directory: Path, patterns: tuple[str, ...]) -> Path | None:
    if not directory.exists():
        return None
    for pattern in patterns:
        matches = sorted(directory.rglob(pattern))
        if matches:
            return matches[0]
    return None


def clean_scalar(value):
    if value is None or pd.isna(value):
        return None
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def frame_records(frame: pd.DataFrame) -> list[dict]:
    return [
        {key: clean_scalar(value) for key, value in record.items()}
        for record in frame.to_dict(orient="records")
    ]


def distribution(series: pd.Series) -> dict:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return {
            "min": None,
            "max": None,
            "mean": None,
            "median": None,
            "q1": None,
            "q3": None,
            "missing_count": int(series.isna().sum()),
            "status": DATA_NOT_AVAILABLE,
        }
    return {
        "min": float(values.min()),
        "max": float(values.max()),
        "mean": float(values.mean()),
        "median": float(values.median()),
        "q1": float(values.quantile(0.25)),
        "q3": float(values.quantile(0.75)),
        "missing_count": int(series.isna().sum()),
        "status": "AVAILABLE",
    }


def write_geojson(frame: gpd.GeoDataFrame, path: Path) -> None:
    """GeoJSON은 웹 전달용으로 항상 WGS84로 저장한다."""
    output = frame.to_crs(WGS84) if frame.crs and frame.crs.to_string() != WGS84 else frame
    output.to_file(path, driver="GeoJSON", encoding="utf-8")

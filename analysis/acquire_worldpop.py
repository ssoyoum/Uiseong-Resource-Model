"""Download a WorldPop 100m population raster for reference analysis."""

from __future__ import annotations

import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import requests

from common import BASE_DIR, DATA_DIR


WORLDPOP_URL = (
    "https://data.worldpop.org/GIS/Population/Global_2015_2030/"
    "R2025A/2020/KOR/v1/100m/constrained/kor_pop_2020_CN_100m_R2025A_v1.tif"
)
OUTPUT_DIR = DATA_DIR / "raw" / "population" / "worldpop"
OUTPUT_PATH = OUTPUT_DIR / "kor_pop_2020_CN_100m_R2025A_v1.tif"
MANIFEST_PATH = DATA_DIR / "manifests" / "worldpop_sources.csv"


def download() -> dict[str, object]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)

    response = requests.get(
        WORLDPOP_URL,
        headers={"User-Agent": "Uiseong-Resource-Model/1.0"},
        stream=True,
        timeout=(30, 300),
    )
    response.raise_for_status()

    sha256 = hashlib.sha256()
    byte_count = 0
    with OUTPUT_PATH.open("wb") as handle:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if not chunk:
                continue
            handle.write(chunk)
            sha256.update(chunk)
            byte_count += len(chunk)

    accessed_at = datetime.now(timezone.utc).isoformat()
    row = {
        "dataset_name": "WorldPop Global2 population count 100m",
        "provider": "WorldPop, University of Southampton",
        "source_url": WORLDPOP_URL,
        "accessed_at": accessed_at,
        "reference_period": "2020",
        "country": "KOR / South Korea",
        "resolution": "100m approximately / 3 arc-seconds",
        "population_type": "constrained population count per grid cell",
        "crs_note": "GeoTIFF CRS is read from the file before spatial use",
        "license_url": "https://www.worldpop.org/data/licence.txt",
        "local_path": str(OUTPUT_PATH.relative_to(BASE_DIR)),
        "bytes": byte_count,
        "sha256": sha256.hexdigest(),
        "status": "AVAILABLE_REFERENCE_ONLY",
        "note": "Reference raster; not a substitute for Korean official resident population statistics",
    }
    fields = list(row)
    with MANIFEST_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow(row)

    return row


if __name__ == "__main__":
    result = download()
    print(f"Downloaded: {result['local_path']}")
    print(f"Bytes: {result['bytes']}")
    print(f"SHA256: {result['sha256']}")

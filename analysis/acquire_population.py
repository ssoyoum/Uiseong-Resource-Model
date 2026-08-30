"""행정안전부 주민등록 연령별 CSV를 data/raw/population에 받는다.

개인정보가 아닌 읍·면·동 단위 집계자료만 받으며, 원자료는 .gitignore로 추적하지 않는다.
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "data" / "raw" / "population"
BASE_URL = "https://jumin.mois.go.kr"


def download_year(year: int) -> Path:
    session = requests.Session()
    session.get(f"{BASE_URL}/ageStatMonth.do", timeout=30).raise_for_status()
    payload = {
        "sltOrgType": "1", "sltOrgLvl1": "A", "sltOrgLvl2": "",
        "gender": "gender", "sum": "sum", "sltUndefType": "",
        "searchYearStart": str(year), "searchMonthStart": "12",
        "searchYearEnd": str(year), "searchMonthEnd": "12",
        "sltOrderType": "1", "sltOrderValue": "ASC",
        "sltArgTypes": "1", "sltArgTypeA": "0", "sltArgTypeB": "100",
        "category": "month",
    }
    response = session.post(
        f"{BASE_URL}/downloadCsvAge.do?searchYearMonth=month&xlsStats=3",
        data=payload,
        timeout=180,
    )
    response.raise_for_status()
    if "octet-stream" not in response.headers.get("content-type", ""):
        raise RuntimeError(f"{year}년 자료 다운로드 응답이 CSV가 아닙니다.")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    target = OUTPUT_DIR / f"mois_age_{year}_1year.csv"
    payload_bytes = response.content
    # The MOIS endpoint has returned both a ZIP containing CSV and a direct
    # CSV attachment over time. Support both formats for fresh clones.
    if zipfile.is_zipfile(io.BytesIO(payload_bytes)):
        with zipfile.ZipFile(io.BytesIO(payload_bytes)) as archive:
            csv_name = next(name for name in archive.namelist() if name.lower().endswith(".csv"))
            target.write_bytes(archive.read(csv_name))
    else:
        target.write_bytes(payload_bytes)
    return target


def main() -> None:
    for year in (2024, 2025):
        path = download_year(year)
        print(f"saved {path.relative_to(ROOT)} ({path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()

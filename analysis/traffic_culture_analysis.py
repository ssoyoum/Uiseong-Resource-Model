"""Extract Uiseong's municipality-level traffic/culture context tables."""

from __future__ import annotations

import csv
import io
import os
import tempfile
import zipfile
from pathlib import Path

import pandas as pd

try:
    from common import ANALYSIS_DIR, BASE_DIR, DATA_DIR, DATA_NOT_AVAILABLE, MANIFEST_DIR, ensure_output_dirs, write_json
except ImportError:
    from analysis.common import ANALYSIS_DIR, BASE_DIR, DATA_DIR, DATA_NOT_AVAILABLE, MANIFEST_DIR, ensure_output_dirs, write_json


SOURCE_DIR = BASE_DIR / "vworld"
TARGET_CODE = "47730"


def find_source(pattern: str) -> Path | None:
    matches = sorted(SOURCE_DIR.glob(pattern)) if SOURCE_DIR.exists() else []
    return matches[0] if matches else None


def definition_columns(path: Path) -> list[str]:
    frame = pd.read_excel(path, header=None)
    header_rows = frame.index[frame.apply(lambda row: row.astype(str).str.strip().eq("컬럼ID").any(), axis=1)]
    if len(header_rows) == 0:
        return []
    header_index = int(header_rows[0])
    columns = []
    for value in frame.iloc[header_index + 1 :, 1].tolist():
        name = str(value).strip()
        if not name or name.lower() == "nan":
            continue
        columns.append(name)
    return columns


def read_table(zip_path: Path, definition_path: Path) -> pd.DataFrame:
    with zipfile.ZipFile(zip_path) as archive:
        members = [name for name in archive.namelist() if name.lower().endswith(".txt")]
        if not members:
            raise ValueError(f"TXT가 없습니다: {zip_path.name}")
        raw = archive.read(members[0])
    frame = pd.read_csv(io.BytesIO(raw), sep="|", header=None, encoding="utf-8-sig", dtype=str)
    frame = frame.apply(lambda column: column.map(lambda value: value.strip() if isinstance(value, str) else value))
    frame = frame.dropna(axis=1, how="all")
    names = definition_columns(definition_path)
    if len(names) < frame.shape[1]:
        names.extend([f"extra_{index:02d}" for index in range(len(names) + 1, frame.shape[1] + 1)])
    frame.columns = names[: frame.shape[1]]
    code_column = "JIJACE_CD"
    frame[code_column] = frame[code_column].astype(str).str.replace(".0", "", regex=False).str.zfill(5)
    return frame.loc[frame[code_column].eq(TARGET_CODE)].copy()


def write_context(table_name: str, zip_pattern: str, definition_pattern: str, output_name: str) -> dict:
    zip_path = find_source(zip_pattern)
    definition_path = find_source(definition_pattern)
    if zip_path is None or definition_path is None:
        return {"dataset": table_name, "status": DATA_NOT_AVAILABLE, "rows": 0, "source_path": ""}
    frame = read_table(zip_path, definition_path)
    output_path = ANALYSIS_DIR / output_name
    frame.to_csv(output_path, index=False, encoding="utf-8-sig")
    return {
        "dataset": table_name,
        "status": "AVAILABLE" if not frame.empty else DATA_NOT_AVAILABLE,
        "rows": int(len(frame)),
        "years": sorted(frame.iloc[:, 0].dropna().astype(str).unique().tolist()),
        "latest_year": str(frame.iloc[:, 0].dropna().astype(str).max()) if not frame.empty else None,
        "municipality_code": TARGET_CODE,
        "source_path": os.path.relpath(zip_path, BASE_DIR).replace("\\", "/"),
        "definition_path": os.path.relpath(definition_path, BASE_DIR).replace("\\", "/"),
        "note": "시군구 단위 배경지표이며 못별 Buffer·도로거리 지표가 아님",
    }


def run() -> dict:
    ensure_output_dirs()
    records = [
        write_context(
            "교통문화지수 항목별 기초통계",
            "T_W_BASE_ART_CULT_IDX.zip",
            "Z_TMACS_T_W_BASE_ART_CULT_IDX.xlsx",
            "traffic_culture_art.csv",
        ),
        write_context(
            "교통문화지수 영역별 통계",
            "T_W_BASE_TRF_CULT_IDX.zip",
            "Z_TMACS_T_W_BASE_TRF_CULT_IDX.xlsx",
            "traffic_culture_trf.csv",
        ),
    ]
    available = [record for record in records if record["status"] == "AVAILABLE"]
    result = {
        "status": "AVAILABLE" if available else DATA_NOT_AVAILABLE,
        "municipality_code": TARGET_CODE,
        "municipality_name": "경북 의성군",
        "datasets": records,
        "use_policy": "의성군 전체 배경지표로만 사용; 개별 시설의 접근성·생활시설 개수로 복제하지 않음",
    }
    write_json(ANALYSIS_DIR / "traffic_culture_context.json", result)

    manifest_path = MANIFEST_DIR / "traffic_culture_sources.csv"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for record in records:
        rows.append({
            "dataset_name": record["dataset"],
            "source_table": record.get("source_path", ""),
            "definition_table": record.get("definition_path", ""),
            "municipality_code": TARGET_CODE,
            "status": record["status"],
            "license_note": "원자료 패키지의 제공기관·재사용 조건 확인 필요",
            "analysis_role": "시군구 단위 배경지표",
        })
    with manifest_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else ["dataset_name"])
        writer.writeheader()
        writer.writerows(rows)
    return result


if __name__ == "__main__":
    result = run()
    print(f"교통문화지수: {result['status']}")

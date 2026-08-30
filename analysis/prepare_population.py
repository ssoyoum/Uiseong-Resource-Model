"""인구 원자료를 표준 스키마로 변환한다.

인구 원자료가 없으면 임의의 수치를 만들지 않고 빈 표와 DATA_NOT_AVAILABLE 상태만 기록한다.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

try:
    from common import (
        ANALYSIS_DIR, DATA_NOT_AVAILABLE, GEOJSON_DIR, MANIFEST_DIR,
        PROCESSED_DIR, ensure_output_dirs, load_geojson, write_json,
    )
except ImportError:  # pragma: no cover - package/direct execution compatibility
    from analysis.common import (
        ANALYSIS_DIR, DATA_NOT_AVAILABLE, GEOJSON_DIR, MANIFEST_DIR,
        PROCESSED_DIR, ensure_output_dirs, load_geojson, write_json,
    )


OUTPUT_COLUMNS = [
    "emd_code", "emd_name", "total_population", "youth_population",
    "youth_ratio", "elderly_population", "elderly_ratio",
    "population_change", "year",
]


ALIASES = {
    "emd_code": ("emd_code", "읍면코드", "행정구역코드", "법정동코드"),
    "emd_name": ("emd_name", "읍면", "읍면명", "행정구역명", "지역명"),
    "total_population": ("total_population", "총인구", "인구수"),
    "youth_population": ("youth_population", "청년인구"),
    "elderly_population": ("elderly_population", "65세이상인구", "고령인구"),
    "population_change": ("population_change", "인구증감", "인구변화"),
    "year": ("year", "기준연도", "연도"),
}


def resolve_column(columns, aliases):
    normalized = {str(column).strip(): column for column in columns}
    for alias in aliases:
        if alias in normalized:
            return normalized[alias]
    return None


def find_population_sources() -> list[Path]:
    raw_dir = Path(__file__).resolve().parents[1] / "data" / "raw" / "population"
    processed_dir = Path(PROCESSED_DIR) / "population"
    mois = sorted(raw_dir.glob("mois_age_*_1year.csv"))
    if mois:
        return mois
    candidates = list(raw_dir.glob("*.csv")) + list(raw_dir.glob("*.xlsx"))
    candidates += [path for path in processed_dir.glob("*.csv") if path.name != "uiseong_population.csv"]
    return sorted(candidates)


def parse_mois_age(source: Path) -> pd.DataFrame | None:
    """행정안전부 연령별 CSV에서 의성군 읍·면 행만 추출한다."""
    try:
        raw = pd.read_csv(source, encoding="cp949", low_memory=False)
    except Exception:
        return None
    if "행정구역" not in raw.columns:
        return None
    total_column = next((column for column in raw.columns if "_계_총인구수" in str(column)), None)
    if total_column is None:
        return None
    age_columns = {}
    for column in raw.columns:
        match = re.search(r"_계_(\d+)세$", str(column))
        if match:
            age_columns[int(match.group(1))] = column
        elif re.search(r"_계_100세 이상$", str(column)):
            age_columns[100] = column
    if not age_columns:
        return None

    region = raw["행정구역"].astype(str)
    code = region.str.extract(r"\((\d{10})\)$")[0]
    mask = code.str.startswith("4773", na=False) & (code != "4773000000")
    filtered = raw.loc[mask].copy()
    if filtered.empty:
        return None
    filtered_region = filtered["행정구역"].astype(str)
    names = filtered_region.str.extract(r"의성군\s+(.+?)\(\d{10}\)$")[0].str.strip()
    numbers = lambda column: pd.to_numeric(filtered[column].astype(str).str.replace(",", "", regex=False), errors="coerce").fillna(0)
    total = numbers(total_column)
    youth = sum((numbers(column) for age, column in age_columns.items() if 19 <= age <= 39), pd.Series(0, index=filtered.index))
    elderly = sum((numbers(column) for age, column in age_columns.items() if age >= 65), pd.Series(0, index=filtered.index))
    year_match = re.search(r"(\d{4})년", str(total_column))
    year = int(year_match.group(1)) if year_match else None
    return pd.DataFrame({
        "emd_code": code.loc[mask].to_numpy(),
        "emd_name": names.to_numpy(),
        "total_population": total.to_numpy(),
        "youth_population": youth.to_numpy(),
        "elderly_population": elderly.to_numpy(),
        "year": year,
    })


def prepare(source: Path | None = None) -> pd.DataFrame:
    ensure_output_dirs()
    sources = [source] if source else find_population_sources()
    status = {"status": DATA_NOT_AVAILABLE, "source": None, "message": "실제 인구 원자료가 data/raw/population에 없습니다."}
    result = pd.DataFrame(columns=OUTPUT_COLUMNS)

    mois_frames = [parse_mois_age(path) for path in sources if path and path.exists()]
    mois_frames = [frame for frame in mois_frames if frame is not None and not frame.empty]
    if mois_frames:
        by_year = pd.concat(mois_frames, ignore_index=True).sort_values("year")
        latest_year = by_year["year"].max()
        result = by_year.loc[by_year["year"] == latest_year].copy()
        previous = by_year.loc[by_year["year"] < latest_year, ["emd_code", "total_population"]]
        if not previous.empty:
            previous = previous.sort_values("emd_code").drop_duplicates("emd_code", keep="last").rename(columns={"total_population": "previous_population"})
            result = result.merge(previous, on="emd_code", how="left")
            result["population_change"] = result["total_population"] - result["previous_population"]
            result = result.drop(columns=["previous_population"])
        else:
            result["population_change"] = pd.NA
        result["youth_ratio"] = result["youth_population"] / result["total_population"] * 100
        result["elderly_ratio"] = result["elderly_population"] / result["total_population"] * 100
        result = result[OUTPUT_COLUMNS].drop_duplicates("emd_code")
        status = {"status": "AVAILABLE", "source": [str(path) for path in sources], "message": "행정안전부 연령별 주민등록 CSV에서 의성군 읍·면 자료를 추출했습니다.", "youth_definition": "만 19~39세", "elderly_definition": "만 65세 이상"}
    elif sources and sources[0] and sources[0].exists():
        source = sources[0]
        raw = pd.read_excel(source) if source.suffix.lower() in {".xlsx", ".xls"} else pd.read_csv(source, encoding="utf-8-sig")
        mapping = {name: resolve_column(raw.columns, aliases) for name, aliases in ALIASES.items()}
        required = ["emd_name", "total_population", "youth_population", "elderly_population"]
        missing = [name for name in required if mapping[name] is None]
        if missing:
            status = {"status": DATA_NOT_AVAILABLE, "source": str(source), "message": f"필수 인구 필드가 없습니다: {missing}"}
        else:
            result = pd.DataFrame({name: raw[column] if column else pd.NA for name, column in mapping.items()})
            for column in ("total_population", "youth_population", "elderly_population", "population_change", "year"):
                result[column] = pd.to_numeric(result[column], errors="coerce")
            result["youth_ratio"] = result["youth_population"] / result["total_population"] * 100
            result["elderly_ratio"] = result["elderly_population"] / result["total_population"] * 100
            result = result[OUTPUT_COLUMNS].dropna(subset=["emd_name"]).drop_duplicates("emd_name")
            if result.empty:
                status = {"status": DATA_NOT_AVAILABLE, "source": str(source), "message": "인구 원자료에 유효한 읍·면 레코드가 없습니다."}
            else:
                status = {"status": "AVAILABLE", "source": str(source), "message": "실제 제공 원자료를 표준 스키마로 변환했습니다."}

    output = PROCESSED_DIR / "population" / "uiseong_population.csv"
    result.to_csv(output, index=False, encoding="utf-8-sig")
    if isinstance(status.get("source"), list):
        status["source"] = [str(Path(item).resolve().relative_to(Path(__file__).resolve().parents[1])).replace("\\", "/") for item in status["source"]]
    elif status.get("source"):
        status["source"] = str(Path(status["source"]).resolve().relative_to(Path(__file__).resolve().parents[1])).replace("\\", "/")
    write_json(ANALYSIS_DIR / "population_input_status.json", status)
    write_json(MANIFEST_DIR / "population_source.json", {
        "status": status["status"],
        "source": status["source"],
        "youth_definition": status.get("youth_definition", "원자료의 youth_population 필드를 그대로 사용; 원자료가 없으면 산출하지 않음"),
        "elderly_definition": status.get("elderly_definition", "원자료의 elderly_population 필드를 그대로 사용; 원자료가 없으면 산출하지 않음"),
        "note": status["message"],
    })

    emd_path = GEOJSON_DIR / "uiseong_emd.geojson"
    if emd_path.exists():
        emd = load_geojson(emd_path)
        emd["population_status"] = status["status"]
        if not result.empty:
            emd = emd.merge(result, left_on="spatial_region", right_on="emd_name", how="left")
        else:
            for column in OUTPUT_COLUMNS:
                if column not in emd:
                    emd[column] = pd.NA
        emd.to_file(GEOJSON_DIR / "uiseong_population.geojson", driver="GeoJSON", encoding="utf-8")
    return result


def main() -> None:
    result = prepare()
    print(f"인구 전처리: {len(result)}개 읍면 레코드 ({'AVAILABLE' if len(result) else DATA_NOT_AVAILABLE})")


if __name__ == "__main__":
    main()

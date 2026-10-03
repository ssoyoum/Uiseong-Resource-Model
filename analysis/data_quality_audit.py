"""산출물 내부 일관성·원자료 무결성·제출 수치 고정 여부를 점검한다.

validation_report.json과 별도 보고서(data_quality_audit.json)로 저장해 기존 제출 수치
(검증 항목 수 포함)를 바꾸지 않는다. 결과값을 고치지 않고 점검만 한다.
"""

from __future__ import annotations

import hashlib
import json

import numpy as np
import pandas as pd

try:
    from common import ANALYSIS_DIR, BASE_DIR, MANIFEST_DIR, PROCESSED_DIR, RAW_DIR, read_json, write_json
except ImportError:
    from analysis.common import ANALYSIS_DIR, BASE_DIR, MANIFEST_DIR, PROCESSED_DIR, RAW_DIR, read_json, write_json


BASELINE_PATH = MANIFEST_DIR / "submission_number_baseline.json"
RAW_CHECKSUM_PATH = MANIFEST_DIR / "raw_checksums.json"
RAW_FILES = [
    "vworld/C_UQ151.zip",
    "vworld/Z_UPIS_C_UQ151.xlsx",
    "vworld/LSMD_CONT_UQ164_5174_경북.zip",
    "vworld/LSMD_CONT_UO601_5174_경북.zip",
    "vworld/T_W_BASE_ART_CULT_IDX.zip",
    "vworld/T_W_BASE_TRF_CULT_IDX.zip",
    "data/raw/population/mois_age_2024_1year.csv",
    "data/raw/population/mois_age_2025_1year.csv",
    "data/raw/population/worldpop/kor_pop_2020_CN_100m_R2025A_v1.tif",
]
RATIO_TOLERANCE = 1e-6


def check(name: str, status: str, details: dict | None = None) -> dict:
    return {"name": name, "status": status, "details": details or {}}


def pass_if(condition: bool, failure: str = "FAIL") -> str:
    return "PASS" if condition else failure


def numeric(frame: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(frame[column], errors="coerce")


def sha256(path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def population_checks() -> list[dict]:
    checks = []
    population = pd.read_csv(PROCESSED_DIR / "population" / "uiseong_population.csv")
    checks.append(check("population_emd_count_18", pass_if(len(population) == 18 and population["emd_code"].is_unique), {"rows": len(population)}))
    total, youth, elderly = (numeric(population, column) for column in ("total_population", "youth_population", "elderly_population"))
    checks.append(check("population_subgroups_within_total", pass_if(bool(((youth + elderly) <= total).all())), {"violations": int(((youth + elderly) > total).sum())}))
    youth_ratio_error = float((numeric(population, "youth_ratio") - youth / total * 100).abs().max())
    elderly_ratio_error = float((numeric(population, "elderly_ratio") - elderly / total * 100).abs().max())
    checks.append(check("population_ratio_recompute", pass_if(max(youth_ratio_error, elderly_ratio_error) < RATIO_TOLERANCE), {"max_abs_error": max(youth_ratio_error, elderly_ratio_error)}))

    year = int(population["year"].max())
    raw_path = RAW_DIR / "population" / f"mois_age_{year}_1year.csv"
    if raw_path.exists():
        raw = pd.read_csv(raw_path, encoding="cp949", low_memory=False)
        total_column = next(column for column in raw.columns if "_계_총인구수" in str(column))
        county = raw.loc[raw["행정구역"].astype(str).str.contains(r"\(4773000000\)"), total_column]
        county_total = int(str(county.iloc[0]).replace(",", "")) if len(county) else None
        checks.append(check(
            "population_emd_sum_equals_county_total",
            pass_if(county_total is not None and int(total.sum()) == county_total),
            {"year": year, "emd_sum": int(total.sum()), "county_total_in_raw": county_total},
        ))
    else:
        checks.append(check("population_emd_sum_equals_county_total", "SKIPPED_RAW_MISSING", {"path": str(raw_path)}))
    return checks


def sgis_checks() -> list[dict]:
    checks = []
    sgis = pd.read_csv(PROCESSED_DIR / "population" / "sgis_drive_population.csv", dtype={"pond_id": str})
    keys = ["pond_id", "sgis_year", "drive_time_min"]
    checks.append(check("sgis_rows_unique_427x2", pass_if(len(sgis) == 854 and not sgis.duplicated(keys).any()), {"rows": len(sgis), "duplicate_keys": int(sgis.duplicated(keys).sum())}))
    available = sgis[sgis["status"] == "AVAILABLE"]
    checks.append(check("sgis_available_population_present", pass_if(bool(numeric(available, "sgis_population").notna().all())), {"available": len(available)}))
    checks.append(check("sgis_population_non_negative", pass_if(bool((numeric(available, "sgis_population") >= 0).all()))))
    missing_rows = sgis[sgis["status"] != "AVAILABLE"]
    checks.append(check("sgis_missing_not_zero_filled", pass_if(bool(numeric(missing_rows, "sgis_population").isna().all())), {"missing_rows": len(missing_rows)}))

    wide = available.pivot_table(index="pond_id", columns="drive_time_min", values=["sgis_population", "service_area_m2"], aggfunc="last")
    both = wide.dropna()
    population_violations = both.index[both[("sgis_population", 5)] > both[("sgis_population", 10)]].tolist()
    area_violations = both.index[both[("service_area_m2", 5)] > both[("service_area_m2", 10)]].tolist()
    checks.append(check("sgis_5min_not_greater_than_10min", pass_if(not population_violations and not area_violations, "WARN"), {
        "ponds_with_both": int(len(both)),
        "population_violations": population_violations,
        "service_area_violations": area_violations,
    }))
    displayed, api_total = numeric(available, "sgis_population"), numeric(available, "sgis_population_api_total")
    relative = ((displayed - api_total).abs() / api_total.replace(0, np.nan)).dropna()
    checks.append(check("sgis_displayed_vs_api_total", "INFO", {
        "compared": int(relative.size),
        "max_relative_diff": round(float(relative.max()), 4) if relative.size else None,
        "over_5_percent": int((relative > 0.05).sum()),
        "note": "SGIS 화면 표시값(비밀보호 처리)과 API 합계의 차이; 분석은 표시값 사용",
    }))
    return checks


def context_checks() -> list[dict]:
    checks = []
    context = pd.read_csv(ANALYSIS_DIR / "pond_context.csv", dtype={"pond_id": str})
    checks.append(check("context_rows_427_unique", pass_if(len(context) == 427 and context["pond_id"].is_unique), {"rows": len(context)}))
    for metric in ("facility_count", "road_length", "agricultural_area"):
        small, large = numeric(context, f"{metric}_500m"), numeric(context, f"{metric}_1000m")
        violations = int((small > large + 1e-6).sum())
        checks.append(check(f"{metric}_500m_le_1km", pass_if(violations == 0), {"violations": violations}))
    for radius in ("500m", "1000m"):
        ratio = numeric(context, f"agricultural_ratio_{radius}")
        checks.append(check(f"agricultural_ratio_{radius}_in_0_100", pass_if(bool(ratio.dropna().between(0, 100 + 1e-6).all())), {"min": float(ratio.min()), "max": float(ratio.max())}))
    official = [column for column in context.columns if column.startswith("official_")]
    filled = {column: int(context[column].notna().sum()) for column in official if context[column].notna().any()}
    checks.append(check("official_population_fields_empty_without_grid", pass_if(not filled), {"filled_columns": filled, "note": "공식 인구격자 미확보 상태에서 값이 생기면 혼용 오류"}))

    worldpop_path = ANALYSIS_DIR / "worldpop_reference_buffer.csv"
    if worldpop_path.exists():
        worldpop = pd.read_csv(worldpop_path, dtype={"pond_id": str})
        violations = int((numeric(worldpop, "worldpop_population_500m") > numeric(worldpop, "worldpop_population_1km") + 1e-6).sum())
        checks.append(check("worldpop_500m_le_1km", pass_if(violations == 0 and len(worldpop) == 427), {"rows": len(worldpop), "violations": violations}))
    return checks


def access_and_classification_checks() -> list[dict]:
    checks = []
    access = pd.DataFrame((read_json(ANALYSIS_DIR / "pond_accessibility.json", {}) or {}).get("data") or [])
    distance = numeric(access, "distance_to_road_m")
    checks.append(check("road_distance_complete_non_negative", pass_if(len(access) == 427 and bool(distance.notna().all()) and bool((distance >= 0).all())), {
        "rows": len(access), "missing": int(distance.isna().sum()), "min_m": float(distance.min()), "max_m": float(distance.max()),
    }))
    # UQ151 기준연도 미확인으로 현재 null. 제출 그림 입력 해시를 보존하기 위해 값은 바꾸지 않고 WARN으로 기록한다.
    checks.append(check("road_source_year_recorded", pass_if(bool(access["road_source_year"].notna().all()), "WARN"), {
        "values": sorted(access["road_source_year"].astype(str).unique().tolist()),
        "note": "UQ151 공식 기준연도 확인 후 accessibility_analysis.py에서 채우고 제출 그림을 재생성해야 함",
    }))
    classes = pd.DataFrame((read_json(ANALYSIS_DIR / "pond_classification.json", {}) or {}).get("data") or [])
    missing_reason = int(classes["classification_reason"].fillna("").astype(str).str.strip().eq("").sum())
    checks.append(check("classification_complete_with_reason", pass_if(len(classes) == 427 and bool(classes["classification_type"].notna().all()) and missing_reason == 0), {
        "rows": len(classes), "missing_reason": missing_reason, "type_counts": classes["classification_type"].value_counts().to_dict(),
    }))
    return checks


def coordinate_checks() -> list[dict]:
    template = pd.read_csv(ANALYSIS_DIR / "coordinate_correction_template.csv", dtype=str, keep_default_na=False)
    correction_columns = ["corrected_x_epsg5174", "corrected_y_epsg5174", "corrected_lat_wgs84", "corrected_lng_wgs84"]
    applied = int((template[correction_columns].apply(lambda column: column.str.strip() != "")).any(axis=1).sum())
    return [check("coordinate_corrections_not_applied", pass_if(applied == 0, "WARN"), {
        "template_rows": len(template), "rows_with_correction": applied,
        "note": "보정 반영 시 SGIS·제출 수치가 바뀌므로 반영 여부를 명시적으로 결정해야 함",
    })]


def current_numbers() -> dict:
    sgis = pd.read_csv(PROCESSED_DIR / "population" / "sgis_drive_population.csv", dtype={"pond_id": str})
    vworld = read_json(ANALYSIS_DIR / "vworld_input_status.json", {}) or {}
    evidence = read_json(ANALYSIS_DIR / "sgis_policy_evidence.json", {}) or {}
    template = pd.read_csv(ANALYSIS_DIR / "coordinate_correction_template.csv", dtype=str)
    population = pd.read_csv(PROCESSED_DIR / "population" / "uiseong_population.csv")
    return {
        "pond_count": int(evidence.get("facility_count", 0)),
        "vworld_facility_count": int(vworld.get("facility_count", 0)),
        "vworld_road_feature_count": int(vworld.get("road_feature_count", 0)),
        "sgis_request_count": int(len(sgis)),
        "sgis_available_count": int((sgis["status"] == "AVAILABLE").sum()),
        "sgis_eligible_unique_coordinate_points": int(evidence.get("eligible_unique_coordinate_points", 0)),
        "sgis_eligible_with_10min_population": int(evidence.get("eligible_with_10min_population", 0)),
        "coordinate_review_count": int(len(template)),
        "emd_count": int(len(population)),
        "population_total_latest": int(population["total_population"].sum()),
    }


def baseline_checks() -> list[dict]:
    numbers = current_numbers()
    if not BASELINE_PATH.exists():
        write_json(BASELINE_PATH, {"note": "제출문서 기준 수치. 의도적으로 변경할 때만 갱신한다.", "numbers": numbers})
        return [check("submission_numbers_frozen", "BASELINE_CREATED", numbers)]
    baseline = (read_json(BASELINE_PATH, {}) or {}).get("numbers", {})
    changed = {key: {"baseline": baseline.get(key), "current": value} for key, value in numbers.items() if baseline.get(key) != value}
    return [check("submission_numbers_frozen", pass_if(not changed), {"changed": changed, "checked": list(numbers)})]


def raw_checksum_checks() -> list[dict]:
    current = {}
    for relative in RAW_FILES:
        path = BASE_DIR / relative
        current[relative] = sha256(path) if path.exists() else None
    if not RAW_CHECKSUM_PATH.exists():
        write_json(RAW_CHECKSUM_PATH, {"algorithm": "sha256", "files": current})
        return [check("raw_checksums_unchanged", "BASELINE_CREATED", {"files": len(current)})]
    baseline = (read_json(RAW_CHECKSUM_PATH, {}) or {}).get("files", {})
    changed = [path for path, digest in current.items() if digest and baseline.get(path) and digest != baseline[path]]
    missing = [path for path, digest in current.items() if digest is None]
    return [check("raw_checksums_unchanged", "FAIL" if changed else ("WARN" if missing else "PASS"), {"changed": changed, "missing_local": missing})]


def run() -> dict:
    checks = []
    for group in (population_checks, sgis_checks, context_checks, access_and_classification_checks, coordinate_checks, baseline_checks, raw_checksum_checks):
        try:
            checks.extend(group())
        except Exception as exc:  # 점검 자체의 실패도 결과로 남긴다.
            checks.append(check(f"{group.__name__}_error", "FAIL", {"error": f"{type(exc).__name__}: {exc}"}))
    counts = pd.Series([item["status"] for item in checks]).value_counts().to_dict()
    report = {
        "status": "FAIL" if counts.get("FAIL") else "PASS",
        "status_counts": counts,
        "checks": checks,
        "note": "validation_report.json과 별도 보고서. 산출값을 수정하지 않고 점검만 수행.",
    }
    write_json(ANALYSIS_DIR / "data_quality_audit.json", report)
    return report


if __name__ == "__main__":
    result = run()
    print(f"data quality audit: {result['status']} {json.dumps(result['status_counts'], ensure_ascii=False)}")

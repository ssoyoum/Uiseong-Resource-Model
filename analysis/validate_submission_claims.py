"""제출 문서의 수치·산출물·미구현 기능 주장을 자동 점검한다."""

from __future__ import annotations

import re
from pathlib import Path

try:
    from common import ANALYSIS_DIR, BASE_DIR, DATA_NOT_AVAILABLE, read_json, write_json
except ImportError:
    from analysis.common import ANALYSIS_DIR, BASE_DIR, DATA_NOT_AVAILABLE, read_json, write_json


REPORT_PATH = ANALYSIS_DIR / "submission_claims_report.json"
DOCUMENT_PATHS = [
    BASE_DIR / "README.md",
    BASE_DIR / "TODO.md",
    BASE_DIR / "docs" / "methodology.md",
    BASE_DIR / "docs" / "implementation-status.md",
]

EXPECTED_OUTPUTS = [
    "data/analysis/validation_report.json",
    "data/analysis/competition/competition_metrics.json",
    "data/analysis/competition/pond_classification.json",
    "data/analysis/competition/pond_context.json",
    "data/analysis/competition/population_summary.json",
    "data/geojson/ponds_classified.geojson",
    "data/geojson/ponds_context.geojson",
    "data/manifests/vworld_sources.csv",
]


def check(name: str, status: str, details: dict | None = None) -> dict:
    return {"name": name, "status": status, "details": details or {}}


def document_text() -> str:
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in DOCUMENT_PATHS
        if path.exists()
    )


def validate_verified_counts(text: str) -> list[dict]:
    report = read_json(ANALYSIS_DIR / "validation_report.json", {}) or {}
    pond_check = next(
        (item for item in report.get("checks", []) if item.get("name") == "pond_count_427"),
        {},
    )
    pond_count = pond_check.get("details", {}).get("actual")
    pond_status = "PASS" if pond_count == 427 and "427" in text else "FAIL"

    vworld_status = read_json(ANALYSIS_DIR / "vworld_input_status.json", {}) or {}
    facility_count = vworld_status.get("facility_count")
    facility_status = "PASS" if facility_count == 68 and "68" in text else "FAIL"

    return [
        check(
            "document_pond_count_427",
            pond_status,
            {"actual": pond_count, "document_contains": "427" in text},
        ),
        check(
            "document_vworld_facility_count_68",
            facility_status,
            {"actual": facility_count, "document_contains": "68" in text},
        ),
    ]


def validate_pipeline_state() -> list[dict]:
    validation = read_json(ANALYSIS_DIR / "validation_report.json", {}) or {}
    access = read_json(ANALYSIS_DIR / "pond_accessibility.json", {}) or {}
    population = read_json(ANALYSIS_DIR / "population_input_status.json", {}) or {}
    vworld = read_json(ANALYSIS_DIR / "vworld_input_status.json", {}) or {}
    road_records = access.get("data", [])
    road_values = sum(row.get("nearest_road_m") is not None for row in road_records)
    roads_available = access.get("status") == "AVAILABLE" and vworld.get("roads_status") == "AVAILABLE"
    return [
        check(
            "validation_report_pass",
            "PASS" if validation.get("status") == "PASS" and validation.get("fail_count") == 0 else "FAIL",
            {"status": validation.get("status"), "fail_count": validation.get("fail_count")},
        ),
        check(
            "roads_claim_status",
            "PASS" if roads_available and road_values > 0 else "FAIL",
            {
                "accessibility": access.get("status"),
                "vworld_roads": vworld.get("roads_status"),
                "distance_value_count": road_values,
            },
        ),
        check(
            "official_population_grid_status",
            "PASS" if population.get("official_grid_status", DATA_NOT_AVAILABLE) == DATA_NOT_AVAILABLE else "WARN",
            {"official_grid_status": population.get("official_grid_status", DATA_NOT_AVAILABLE)},
        ),
    ]


def validate_outputs() -> list[dict]:
    checks = []
    for relative_path in EXPECTED_OUTPUTS:
        path = BASE_DIR / relative_path
        checks.append(
            check(
                f"output_exists:{relative_path}",
                "PASS" if path.exists() else "FAIL",
                {"path": relative_path},
            )
        )
    return checks


def validate_unsupported_claims(text: str) -> list[dict]:
    unsupported_patterns = {
        "unverified_accuracy": r"정확도\s*87\.2%|F1\s*0\.85",
        "unverified_field_reduction": r"88\.3%\s*(절감|감소)",
        "unverified_rf_completion": r"GeoAI\s*자동분류\s*모델\s*구현\s*완료",
        "unverified_realtime_completion": r"실시간\s*(?:VWorld\s*)?연동\s*구현\s*완료",
    }
    checks = []
    for name, pattern in unsupported_patterns.items():
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        checks.append(
            check(
                f"unsupported_claim:{name}",
                "PASS" if not matches else "FAIL",
                {"match_count": len(matches)},
            )
        )
    return checks


def run() -> dict:
    text = document_text()
    checks = []
    checks.extend(validate_verified_counts(text))
    checks.extend(validate_pipeline_state())
    checks.extend(validate_outputs())
    checks.extend(validate_unsupported_claims(text))
    failed = sum(item["status"] == "FAIL" for item in checks)
    report = {
        "status": "PASS" if failed == 0 else "FAIL",
        "pass_count": sum(item["status"] == "PASS" for item in checks),
        "warn_count": sum(item["status"] == "WARN" for item in checks),
        "fail_count": failed,
        "documents_checked": [path.relative_to(BASE_DIR).as_posix() for path in DOCUMENT_PATHS if path.exists()],
        "checks": checks,
        "note": "미확보 데이터는 DATA_NOT_AVAILABLE 상태를 유지하는지 함께 점검합니다.",
    }
    write_json(REPORT_PATH, report)
    return report


def main() -> None:
    report = run()
    print(
        f"제출문서 점검: {report['status']} "
        f"(pass={report['pass_count']}, warn={report['warn_count']}, fail={report['fail_count']})"
    )


if __name__ == "__main__":
    main()

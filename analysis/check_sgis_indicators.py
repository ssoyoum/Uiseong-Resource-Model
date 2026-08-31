"""Check which documented SGIS regional indicators return data for Uiseong.

The check records only endpoint metadata and counts. It never writes tokens or
raw SGIS responses. A no-result response is recorded as DATA_NOT_AVAILABLE;
it is not converted into zero.
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any

try:
    from common import write_json
    from sgis_api import (
        COMPANY_URL,
        HOUSEHOLD_URL,
        HOUSE_URL,
        POPULATION_URL,
        SEARCH_POPULATION_URL,
        _get_json,
        authenticate,
    )
except ImportError:
    from analysis.common import write_json
    from analysis.sgis_api import (
        COMPANY_URL,
        HOUSEHOLD_URL,
        HOUSE_URL,
        POPULATION_URL,
        SEARCH_POPULATION_URL,
        _get_json,
        authenticate,
    )


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "data" / "analysis" / "sgis_indicator_availability.json"

INDICATORS = (
    ("population", POPULATION_URL, {"low_search": 1}),
    ("age_population", SEARCH_POPULATION_URL, {"gender": 0, "low_search": 1, "age_type": 0}),
    ("household", HOUSEHOLD_URL, {"low_search": 1}),
    ("housing", HOUSE_URL, {"low_search": 1}),
    ("company_workers", COMPANY_URL, {"low_search": 1}),
)


def result_count(result: Any) -> int | None:
    if isinstance(result, list):
        return len(result)
    if isinstance(result, dict):
        for value in result.values():
            if isinstance(value, list):
                return len(value)
    return None


def probe(token: str, name: str, endpoint: str, year: int, adm_cd: str, extra: dict[str, Any]) -> dict[str, Any]:
    params = {"accessToken": token, "year": year, "adm_cd": adm_cd, **extra}
    payload = _get_json(endpoint, params)
    err_cd = payload.get("errCd")
    count = result_count(payload.get("result"))
    if str(err_cd) == "0" and (count is None or count > 0):
        status = "AVAILABLE"
    elif str(err_cd) in {"0", "-100"}:
        status = "DATA_NOT_AVAILABLE"
    else:
        status = "API_ERROR"
    return {
        "indicator": name,
        "endpoint": endpoint,
        "year": year,
        "adm_cd": adm_cd,
        "status": status,
        "errCd": err_cd,
        "errMsg": payload.get("errMsg"),
        "record_count": count,
    }


def run(years: list[int], adm_cd: str) -> dict[str, Any]:
    token, _ = authenticate()
    checks: list[dict[str, Any]] = []
    for year in years:
        for name, endpoint, extra in INDICATORS:
            try:
                checks.append(probe(token, name, endpoint, year, adm_cd, extra))
            except Exception as exc:  # preserve endpoint-specific failures and continue
                checks.append(
                    {
                        "indicator": name,
                        "endpoint": endpoint,
                        "year": year,
                        "adm_cd": adm_cd,
                        "status": "API_ERROR",
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                )
    available = [item for item in checks if item["status"] == "AVAILABLE"]
    status = {
        "checked_at": date.today().isoformat(),
        "scope": {"adm_cd": adm_cd, "years": years},
        "authentication": "PASS",
        "checks": checks,
        "summary": {
            "checked": len(checks),
            "available": len(available),
            "data_not_available": sum(item["status"] == "DATA_NOT_AVAILABLE" for item in checks),
            "api_error": sum(item["status"] == "API_ERROR" for item in checks),
        },
        "selection": {
            "primary_sgis_indicator": "SGIS 생활권역 serviceAreaStatistics: 2024년 5·10분 주행생활권 인구",
            "primary_output": "data/processed/population/sgis_drive_population.csv",
            "regional_census_indicators": "Use only when this check reports AVAILABLE for the requested Uiseong code/year.",
            "no_result_rule": "DATA_NOT_AVAILABLE is retained as missing; it is never converted to zero or imputed.",
        },
        "source": "SGIS OpenAPI documented census statistics endpoints",
    }
    write_json(OUTPUT_PATH, status)
    return status


def main() -> None:
    parser = argparse.ArgumentParser(description="Check SGIS regional indicator availability")
    parser.add_argument("--year", nargs="+", type=int, default=[2020, 2024])
    parser.add_argument("--adm-cd", default="47730")
    args = parser.parse_args()
    status = run(args.year, args.adm_cd)
    print(json.dumps(status["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

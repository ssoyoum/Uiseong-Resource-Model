"""Small, credential-safe client for the SGIS OpenAPI.

Credentials are read from process environment variables first and then from
the repository-root ``.env`` file. Tokens and credentials are never printed or
written to an output file.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
AUTH_URL = "https://sgisapi.mods.go.kr/OpenAPI3/auth/authentication.json"
POPULATION_URL = "https://sgisapi.mods.go.kr/OpenAPI3/stats/population.json"
SEARCH_POPULATION_URL = "https://sgisapi.mods.go.kr/OpenAPI3/stats/searchpopulation.json"
HOUSEHOLD_URL = "https://sgisapi.mods.go.kr/OpenAPI3/stats/household.json"
HOUSE_URL = "https://sgisapi.mods.go.kr/OpenAPI3/stats/house.json"
COMPANY_URL = "https://sgisapi.mods.go.kr/OpenAPI3/stats/company.json"
SERVICE_AREA_GEOMETRY_URL = (
    "https://sgis.mods.go.kr/ServiceAPI/OpenAPI3/catchmentArea/serviceAreaGeometry.json"
)
SERVICE_AREA_STATISTICS_URL = (
    "https://sgis.mods.go.kr/ServiceAPI/OpenAPI3/catchmentArea/serviceAreaStatistics.json"
)
STATUS_PATH = ROOT / "data" / "analysis" / "sgis_api_status.json"


class SgisApiError(RuntimeError):
    """An expected SGIS API or credential error."""


class SgisNoDataError(SgisApiError):
    """SGIS could not build a route area for the requested point."""


def _read_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        line = re.sub(r"^export\s+", "", line)
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$", line)
        if not match:
            continue
        value = match.group(2).strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'\"', "'"}:
            value = value[1:-1]
        values[match.group(1)] = value
    return values


def credentials() -> tuple[str, str]:
    local = _read_dotenv(ROOT / ".env")
    key = os.environ.get("SGIS_CONSUMER_KEY", local.get("SGIS_CONSUMER_KEY", ""))
    secret = os.environ.get("SGIS_CONSUMER_SECRET", local.get("SGIS_CONSUMER_SECRET", ""))
    if not key or not secret:
        raise SgisApiError(
            "SGIS_CONSUMER_KEY and SGIS_CONSUMER_SECRET are required in .env "
            "or the process environment."
        )
    return key, secret


def _get_json(url: str, params: dict[str, Any], timeout: int = 30) -> dict[str, Any]:
    query = urlencode({key: str(value) for key, value in params.items()})
    request = Request(f"{url}?{query}", headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise SgisApiError(f"SGIS HTTP error: {exc.code}") from exc
    except (URLError, TimeoutError) as exc:
        raise SgisApiError(f"SGIS connection error: {exc.reason if hasattr(exc, 'reason') else exc}") from exc
    except json.JSONDecodeError as exc:
        raise SgisApiError("SGIS returned a non-JSON response") from exc
    if not isinstance(payload, dict):
        raise SgisApiError("SGIS returned an unexpected response shape")
    return payload


def _post_json(url: str, params: dict[str, Any], timeout: int = 120) -> dict[str, Any]:
    body = urlencode({key: str(value) for key, value in params.items()}).encode("utf-8")
    request = Request(
        url,
        data=body,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise SgisApiError(f"SGIS HTTP error: {exc.code}") from exc
    except (URLError, TimeoutError) as exc:
        raise SgisApiError(f"SGIS connection error: {exc.reason if hasattr(exc, 'reason') else exc}") from exc
    except json.JSONDecodeError as exc:
        raise SgisApiError("SGIS returned a non-JSON response") from exc
    if not isinstance(payload, dict):
        raise SgisApiError("SGIS returned an unexpected response shape")
    return payload


def service_area_geometry(
    token: str,
    x: float,
    y: float,
    minutes: list[int],
) -> dict[str, Any]:
    """Request SGIS route-based polygons for one point.

    SGIS internally subtracts four seconds from time breaks before routing;
    the returned attributes are restored by the web client. We follow that
    behavior so a requested 5-minute break uses 296 seconds internally.
    """
    facilities = json.dumps(
        {
            "features": [
                {
                    "geometry": {
                        "x": x,
                        "y": y,
                        "spatialReference": {"wkid": 5179, "latestWkid": 5179},
                    }
                }
            ]
        },
        separators=(",", ":"),
    )
    params = {
        "f": "json",
        "facilities": facilities,
        "impedanceAttributeName": "LEAD_TIME",
        "defaultBreaks": ",".join(str(max(1, int(value) * 60 - 4)) for value in minutes),
        "outSR": "5179",
        "returnFacilities": "false",
        "returnBarriers": "false",
        "returnPolylineBarriers": "false",
        "returnPolygonBarriers": "false",
        "outputLines": "esriNAOutputLineNone",
        "outputPolygons": "esriNAOutputPolygonSimplified",
    }
    payload = _get_json(SERVICE_AREA_GEOMETRY_URL, params, timeout=120)
    if str(payload.get("errCd")) != "0":
        raise SgisApiError(f"SGIS service-area geometry failed: errCd={payload.get('errCd')}")
    try:
        result = json.loads(str(payload["result"]))
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise SgisApiError("SGIS service-area geometry returned an unexpected shape") from exc
    if isinstance(result, dict) and result.get("error"):
        details = result["error"].get("details") or []
        raise SgisNoDataError(str(details[0] if details else "no route area"))
    try:
        features = result["saPolygons"]["features"]
    except (KeyError, TypeError) as exc:
        raise SgisApiError("SGIS service-area geometry returned an unexpected shape") from exc
    if not features:
        raise SgisNoDataError("SGIS service-area geometry returned no polygons")
    return {"features": features, "requested_minutes": minutes}


def service_area_statistics(
    token: str,
    area_wkt: str,
    year: int,
    class_degree: int = 11,
) -> dict[str, Any]:
    payload = _post_json(
        SERVICE_AREA_STATISTICS_URL,
        {
            "accessToken": token,
            "classDeg": class_degree,
            "base_year": year,
            "copr_base_year": year,
            "area": area_wkt,
            "srvAreaType": 1,
            "workGb": "all",
        },
        timeout=180,
    )
    if str(payload.get("errCd")) != "0":
        raise SgisApiError(f"SGIS service-area statistics failed: errCd={payload.get('errCd')}")
    return payload


def authenticate() -> tuple[str, dict[str, Any]]:
    key, secret = credentials()
    payload = _get_json(AUTH_URL, {"consumer_key": key, "consumer_secret": secret})
    if str(payload.get("errCd")) != "0":
        raise SgisApiError(f"SGIS authentication failed: errCd={payload.get('errCd')}")
    result = payload.get("result") or {}
    token = result.get("accessToken")
    if not token:
        raise SgisApiError("SGIS authentication succeeded without an access token")
    return str(token), payload


def population(year: int = 2020, adm_cd: str = "47730", low_search: int = 1) -> dict[str, Any]:
    token, _ = authenticate()
    payload = _get_json(
        POPULATION_URL,
        {"accessToken": token, "year": year, "adm_cd": adm_cd, "low_search": low_search},
    )
    if str(payload.get("errCd")) != "0":
        raise SgisApiError(
            f"SGIS population API failed: errCd={payload.get('errCd')}, "
            f"errMsg={payload.get('errMsg')}"
        )
    return payload


def write_status(status: dict[str, Any]) -> None:
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Credential-safe SGIS API checks")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("auth-check", help="authenticate without printing the token")
    population_parser = subparsers.add_parser("population-check", help="call the documented population API")
    population_parser.add_argument("--year", type=int, default=2020)
    population_parser.add_argument("--adm-cd", default="47730")
    args = parser.parse_args(argv)

    try:
        if args.command == "auth-check":
            _, payload = authenticate()
            result = payload.get("result") or {}
            status = {
                "status": "PASS",
                "endpoint": AUTH_URL,
                "errCd": payload.get("errCd"),
                "token_received": True,
                "access_timeout": result.get("accessTimeout"),
            }
            print("SGIS authentication: PASS (token received; token omitted)")
        else:
            payload = population(args.year, args.adm_cd)
            records = payload.get("result") or []
            status = {
                "status": "PASS",
                "endpoint": POPULATION_URL,
                "errCd": payload.get("errCd"),
                "year": args.year,
                "adm_cd": args.adm_cd,
                "record_count": len(records) if isinstance(records, list) else None,
                "source": "SGIS OpenAPI population statistics",
            }
            print(f"SGIS population API: PASS (records={status['record_count']}; response not persisted)")
        write_status(status)
        return 0
    except SgisApiError as exc:
        status = {"status": "FAIL", "error": str(exc)}
        write_status(status)
        print(f"SGIS API check: FAIL ({exc})", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

"""좌표 보정 대상 못의 지번주소를 SGIS 공식 지오코더로 조회해 후보 좌표를 만든다.

결과는 검토용 후보 파일에만 저장하고 coordinate_correction_template.csv에는 쓰지 않는다.
검토자가 후보를 확인한 뒤 템플릿에 옮겨야 분석에 반영된다.
"""

from __future__ import annotations

import re
import time

import geopandas as gpd
import pandas as pd
from pyproj import Transformer
from shapely.geometry import Point

try:
    from common import ANALYSIS_CRS, ANALYSIS_DIR, GEOJSON_DIR, load_geojson, write_json
    from sgis_api import SgisApiError, _get_json, authenticate
except ImportError:
    from analysis.common import ANALYSIS_CRS, ANALYSIS_DIR, GEOJSON_DIR, load_geojson, write_json
    from analysis.sgis_api import SgisApiError, _get_json, authenticate


GEOCODE_URL = "https://sgisapi.mods.go.kr/OpenAPI3/addr/geocode.json"
TEMPLATE_PATH = ANALYSIS_DIR / "coordinate_correction_template.csv"
OUTPUT_PATH = ANALYSIS_DIR / "coordinate_geocode_candidates.csv"
SUMMARY_PATH = ANALYSIS_DIR / "coordinate_geocode_candidates.json"
ADDRESS_PREFIX = "경상북도 의성군"
SGIS_CRS = "EPSG:5179"
SGIS_NO_RESULT = "-100"
# 지번 뒤에 붙은 지목 약어(유=유지, 답, 구=구거, 임=임야 등)
LAND_CATEGORY_SUFFIX = r"(유|답|구|임|전|대|천|제|도|잡|목|과|장|학|종|묘|공|체|수|철|창|주|광|염|원|양|사)$"
ADDRESS_PATTERN = re.compile(r"^(?P<area>.+?[리동])\s*(?P<mountain>산)?\s*(?P<main>\d+)(?:-(?P<sub>\d+))?\s*(?P<category>\S*)$")


def parse_address(address: str) -> dict | None:
    text = re.sub(r"\s+", " ", str(address or "")).strip()
    match = ADDRESS_PATTERN.match(text)
    if not match:
        return None
    category = match.group("category") or ""
    if category and not re.fullmatch(LAND_CATEGORY_SUFFIX, category):
        return None
    main = str(int(match.group("main")))
    sub = str(int(match.group("sub"))) if match.group("sub") else ""
    mountain = bool(match.group("mountain"))
    lot = f"{'산 ' if mountain else ''}{main}{'-' + sub if sub else ''}"
    return {
        "query_address": f"{ADDRESS_PREFIX} {match.group('area')} {lot}",
        "area": match.group("area"),
        "mountain": mountain,
        "main": main,
        "sub": sub,
        "land_category": category,
    }


def normalize_lot(value) -> str:
    text = str(value or "").strip()
    return "" if text.lower() == "null" else text


def is_exact_parcel(parsed: dict, row: dict) -> bool:
    returned_main = normalize_lot(row.get("jibun_main_no"))
    expected_main = f"산 {parsed['main']}" if parsed["mountain"] else parsed["main"]
    returned_sub = normalize_lot(row.get("jibun_sub_no"))
    area_ok = parsed["area"].split()[-1] == normalize_lot(row.get("ri_nm")) or parsed["area"].split()[-1] == normalize_lot(row.get("adm_nm"))
    return area_ok and returned_main == expected_main and returned_sub == parsed["sub"]


def run(pause_seconds: float = 0.2) -> dict:
    template = pd.read_csv(TEMPLATE_PATH, dtype=str, keep_default_na=False)
    boundary = load_geojson(GEOJSON_DIR / "uiseong_boundary.geojson", ANALYSIS_CRS)
    boundary_union = boundary.geometry.union_all() if hasattr(boundary.geometry, "union_all") else boundary.geometry.unary_union
    to_analysis = Transformer.from_crs(SGIS_CRS, ANALYSIS_CRS, always_xy=True)
    to_wgs84 = Transformer.from_crs(SGIS_CRS, "EPSG:4326", always_xy=True)
    emd = load_geojson(GEOJSON_DIR / "uiseong_emd.geojson", ANALYSIS_CRS)

    def emd_at(point: Point) -> str:
        hits = emd.loc[emd.geometry.covers(point), "spatial_region"].tolist()
        return hits[0] if hits else ""

    token, _ = authenticate()

    rows = []
    for record in template.to_dict(orient="records"):
        parsed = parse_address(record["address"])
        item = {
            "pond_id": record["pond_id"],
            "address": record["address"],
            "review_reason": record.get("review_reason", ""),
            "query_address": parsed["query_address"] if parsed else "",
            "geocode_status": "ADDRESS_PARSE_FAILED" if not parsed else "",
            "candidate_x_epsg5174": None,
            "candidate_y_epsg5174": None,
            "candidate_lat_wgs84": None,
            "candidate_lng_wgs84": None,
            "returned_lot": "",
            "shift_from_current_m": None,
            "inside_uiseong_boundary": None,
            "candidate_emd": "",
            "emd_matches_address": None,
            "suggested_confidence": "",
        }
        if parsed:
            try:
                payload = _get_json(GEOCODE_URL, {
                    "accessToken": token, "address": parsed["query_address"], "pagenum": 0, "resultcount": 5,
                })
            except SgisApiError as exc:
                payload = {"errCd": "HTTP", "errMsg": str(exc)}
            results = ((payload.get("result") or {}).get("resultdata") or []) if str(payload.get("errCd")) == "0" else []
            exact = [row for row in results if is_exact_parcel(parsed, row)]
            chosen = exact[0] if exact else None
            if str(payload.get("errCd")) == SGIS_NO_RESULT:
                item["geocode_status"] = "NO_RESULT"
            elif str(payload.get("errCd")) != "0":
                item["geocode_status"] = f"API_ERROR_{payload.get('errCd')}"
            elif not results:
                item["geocode_status"] = "NO_RESULT"
            elif not chosen:
                item["geocode_status"] = "NO_EXACT_PARCEL_MATCH"
                first = results[0]
                item["returned_lot"] = f"{normalize_lot(first.get('ri_nm'))} {normalize_lot(first.get('jibun_main_no'))}-{normalize_lot(first.get('jibun_sub_no'))}".strip("- ")
            else:
                item["geocode_status"] = "EXACT_PARCEL_MATCH" if len(exact) == 1 else "MULTIPLE_EXACT_MATCHES"
                sgis_x, sgis_y = float(chosen["x"]), float(chosen["y"])
                x, y = to_analysis.transform(sgis_x, sgis_y)
                lng, lat = to_wgs84.transform(sgis_x, sgis_y)
                current = pd.to_numeric(pd.Series([record.get("current_x"), record.get("current_y")]), errors="coerce")
                item.update({
                    "candidate_x_epsg5174": round(x, 3),
                    "candidate_y_epsg5174": round(y, 3),
                    "candidate_lat_wgs84": round(lat, 7),
                    "candidate_lng_wgs84": round(lng, 7),
                    "returned_lot": f"{normalize_lot(chosen.get('ri_nm'))} {normalize_lot(chosen.get('jibun_main_no'))}{'-' + normalize_lot(chosen.get('jibun_sub_no')) if normalize_lot(chosen.get('jibun_sub_no')) else ''}",
                    "shift_from_current_m": round(Point(x, y).distance(Point(current[0], current[1])), 1) if current.notna().all() else None,
                    "inside_uiseong_boundary": bool(boundary_union.covers(Point(x, y))),
                    "candidate_emd": emd_at(Point(x, y)),
                })
                item["emd_matches_address"] = item["candidate_emd"] == parsed["area"].split()[0]
                # 지번 중심 좌표이므로 현장 확인 전에는 MEDIUM을 넘기지 않는다.
                consistent = item["geocode_status"] == "EXACT_PARCEL_MATCH" and item["inside_uiseong_boundary"] and item["emd_matches_address"]
                item["suggested_confidence"] = "MEDIUM" if consistent else "LOW"
            time.sleep(pause_seconds)
        rows.append(item)

    result = pd.DataFrame(rows)
    duplicated = result["candidate_x_epsg5174"].notna() & result.duplicated(["candidate_x_epsg5174", "candidate_y_epsg5174"], keep=False)
    result["shares_candidate_with_other_pond"] = duplicated
    result["correction_source"] = result["geocode_status"].map(
        lambda status: "SGIS 주소 지오코딩 API(addr/geocode) 지번 일치" if status == "EXACT_PARCEL_MATCH" else ""
    )
    result.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    summary = {
        "status": "CANDIDATES_ONLY_NOT_APPLIED",
        "source": "SGIS OpenAPI addr/geocode (통계청)",
        "input": "data/analysis/coordinate_correction_template.csv",
        "output": "data/analysis/coordinate_geocode_candidates.csv",
        "record_count": int(len(result)),
        "status_counts": result["geocode_status"].value_counts().to_dict(),
        "exact_match_inside_boundary": int(((result["geocode_status"] == "EXACT_PARCEL_MATCH") & (result["inside_uiseong_boundary"] == True)).sum()),
        "emd_mismatch_ponds": result.loc[result["emd_matches_address"] == False, "pond_id"].tolist(),
        "suggested_confidence_counts": result["suggested_confidence"].replace("", "NONE").value_counts().to_dict(),
        "shared_candidate_ponds": result.loc[duplicated, "pond_id"].tolist(),
        "shift_from_current_m": result["shift_from_current_m"].dropna().describe().round(1).to_dict(),
        "method": "지목 약어를 제거한 지번주소를 조회하고, 반환된 리·본번·부번이 입력과 모두 일치할 때만 후보로 채택",
        "note": "지번(필지) 대표좌표이며 못 수면 위치와 다를 수 있다. 템플릿에 자동 반영하지 않으며, 검토 후 반영 시 SGIS 주행인구 재수집이 필요하다.",
    }
    write_json(SUMMARY_PATH, summary)
    return summary


if __name__ == "__main__":
    output = run()
    print(f"좌표 후보: {output['status_counts']}")

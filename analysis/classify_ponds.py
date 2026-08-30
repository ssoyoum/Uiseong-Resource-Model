"""검증 가능한 규칙 기반으로 못 활용유형을 분류한다.

임의의 종합점수 대신 충분한 입력이 있는 경우에만 규칙을 적용하고, 그렇지 않으면
보수적 보존·기록형으로 표시한다. 모든 시설의 분류근거를 함께 저장한다.
"""

from __future__ import annotations

import pandas as pd

try:
    from common import (
        ANALYSIS_DIR, DATA_NOT_AVAILABLE, GEOJSON_DIR, distribution,
        ensure_output_dirs, frame_records, load_ponds, read_json, write_geojson, write_json,
    )
except ImportError:
    from analysis.common import (
        ANALYSIS_DIR, DATA_NOT_AVAILABLE, GEOJSON_DIR, distribution,
        ensure_output_dirs, frame_records, load_ponds, read_json, write_geojson, write_json,
    )


TYPE_LABELS = {
    "A_CULTURE_TOURISM": "문화·관광형",
    "B_ECO_EDUCATION": "생태·교육형",
    "C_COMMUNITY": "공동체형",
    "D_PRESERVATION": "보존·기록형",
    "E_MANAGEMENT_PRIORITY": "관리우선형",
}


def run() -> pd.DataFrame:
    ensure_output_dirs()
    ponds = load_ponds()
    context_path = ANALYSIS_DIR / "pond_context.csv"
    access_path = ANALYSIS_DIR / "pond_accessibility.csv"
    context = pd.read_csv(context_path) if context_path.exists() else pd.DataFrame()
    access = pd.read_csv(access_path) if access_path.exists() else pd.DataFrame()
    result = ponds.drop(columns=["geometry"], errors="ignore").copy()
    result["id"] = result["id"].astype(str)
    if not context.empty:
        context["pond_id"] = context["pond_id"].astype(str)
        result = result.merge(context, left_on="id", right_on="pond_id", how="left", suffixes=("", "_context"))
    if not access.empty:
        access["pond_id"] = access["pond_id"].astype(str)
        result = result.merge(access, left_on="id", right_on="pond_id", how="left", suffixes=("", "_access"))

    agriculture = pd.to_numeric(result.get("agricultural_ratio_1000m"), errors="coerce") if "agricultural_ratio_1000m" in result else pd.Series(dtype=float)
    road = pd.to_numeric(result.get("nearest_road_m"), errors="coerce") if "nearest_road_m" in result else pd.Series(dtype=float)
    facility_count = pd.to_numeric(result.get("facility_count_1000m"), errors="coerce") if "facility_count_1000m" in result else pd.Series(dtype=float)
    elderly = pd.to_numeric(result.get("elderly_population_1000m"), errors="coerce") if "elderly_population_1000m" in result else pd.Series(dtype=float)
    agriculture_q3 = agriculture.quantile(0.75) if agriculture.notna().any() else None
    classifications = []
    reasons = []

    for index, row in result.iterrows():
        management = str(row.get("management", ""))
        if management and management not in {"미기재", "nan", "None"} and management.lower() in {"bad", "poor", "불량", "미흡"}:
            classifications.append("E_MANAGEMENT_PRIORITY")
            reasons.append("관리상태가 낮은 것으로 기록되어 관리우선형으로 분류")
        elif pd.notna(road.get(index)) and pd.notna(facility_count.get(index)) and road.get(index) <= 300 and facility_count.get(index) > 0:
            classifications.append("A_CULTURE_TOURISM")
            reasons.append(f"도로 {road.get(index):.0f}m 이내이며 1km 생활시설 {facility_count.get(index):.0f}개")
        elif agriculture_q3 is not None and pd.notna(agriculture.get(index)) and agriculture.get(index) >= agriculture_q3 and pd.notna(road.get(index)) and road.get(index) > 500:
            classifications.append("B_ECO_EDUCATION")
            reasons.append("1km 농업지역 비율 상위 25%이고 도로 접근성이 낮음")
        elif pd.notna(elderly.get(index)) and pd.notna(road.get(index)) and road.get(index) <= 300:
            classifications.append("C_COMMUNITY")
            reasons.append("주변 고령인구 수요와 접근성 자료가 함께 확인됨")
        else:
            classifications.append("D_PRESERVATION")
            reasons.append("현재 확보된 자료만으로 활동형 판정에 필요한 인구·도로·생활시설 근거가 부족하여 보존·기록형으로 보수적 표시")

    result["classification_type"] = classifications
    result["classification_label"] = result["classification_type"].map(TYPE_LABELS)
    result["classification_reason"] = reasons
    result["classification_status"] = "RULE_BASED_WITH_MISSING_DATA_GUARD"
    result.to_csv(ANALYSIS_DIR / "pond_classification.csv", index=False, encoding="utf-8-sig")

    variables = {}
    for column in ("capacity", "nearest_road_m", "agricultural_ratio_500m", "agricultural_ratio_1000m", "population_500m", "population_1km", "facility_count_500m", "facility_count_1000m"):
        if column in result:
            variables[column] = distribution(result[column])
    write_json(ANALYSIS_DIR / "classification_variable_distributions.json", variables)
    summary = result["classification_type"].value_counts().rename_axis("classification_type").reset_index(name="facility_count")
    write_json(ANALYSIS_DIR / "pond_classification_summary.json", {
        "status": "AVAILABLE",
        "method": "규칙 기반; 충분한 검증 입력이 없는 시설은 D_PRESERVATION으로 보수적 표시",
        "types": frame_records(summary),
        "missing_data_policy": DATA_NOT_AVAILABLE,
    })
    write_json(ANALYSIS_DIR / "pond_classification.json", {
        "status": "AVAILABLE",
        "method": "규칙 기반; 충분한 검증 입력이 없는 시설은 D_PRESERVATION으로 보수적 표시",
        "data": frame_records(result),
    })

    geo = load_ponds()
    properties = result.set_index("id").to_dict(orient="index")
    for index, feature_id in enumerate(geo["id"].astype(str)):
        for key, value in properties.get(feature_id, {}).items():
            if key not in {"geometry", "id"}:
                geo.loc[index, key] = value
    write_geojson(geo, GEOJSON_DIR / "ponds_classified.geojson")
    return result


def main() -> None:
    result = run()
    print(f"못 활용유형 분류: {len(result)}개 시설")


if __name__ == "__main__":
    main()

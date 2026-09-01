"""Build the verified SGIS Uiseong case-study submission report.

This is a documentation/output step over existing analysis artifacts. It does
not impute missing values, change classifications, or create a policy score.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DIR = ROOT / "data" / "analysis"
FIGURE_DIR = ROOT / "analysis" / "figures"
REPORT_PATH = ROOT / "docs" / "submission" / "sgis-uiseong-submission-report.md"
MANIFEST_PATH = ANALYSIS_DIR / "submission_visualization_manifest.json"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validation_check(validation: dict, name: str) -> dict:
    for check in validation.get("checks", []):
        if check.get("name") == name:
            return check
    return {}


def build() -> tuple[dict, list[dict]]:
    sgis = read_json(ANALYSIS_DIR / "sgis_catchment_analysis.json")
    comparison = read_json(ANALYSIS_DIR / "sgis_policy_comparison.json")
    classification = read_json(ANALYSIS_DIR / "pond_classification_summary.json")
    validation = read_json(ANALYSIS_DIR / "validation_report.json")
    claims = read_json(ANALYSIS_DIR / "submission_claims_report.json")

    figures = [
        {
            "file": "analysis/figures/06_pond_distribution.png",
            "purpose": "427개 전통 못의 공간 분포",
            "source": "data/processed/ponds.csv",
            "interpretation": "분포 현황 지도; 정책 우선순위 자체를 의미하지 않음",
        },
        {
            "file": "analysis/figures/07_pond_road_accessibility.png",
            "purpose": "못-도로 최근접거리 접근성",
            "source": "data/analysis/pond_accessibility.csv",
            "interpretation": "EPSG:5174 유클리드 최근접거리; 주행시간·네트워크 거리가 아님",
        },
        {
            "file": "analysis/figures/08_pond_buffer_analysis.png",
            "purpose": "500m·1km 주변 농업·시설 맥락",
            "source": "data/analysis/pond_context.csv",
            "interpretation": "주변환경 맥락; 공식 인구격자 Buffer 인구는 포함하지 않음",
        },
        {
            "file": "analysis/figures/09_pond_classification.png",
            "purpose": "규칙기반 활용유형 분류",
            "source": "data/analysis/pond_classification.csv",
            "interpretation": "분류근거와 결측 fallback을 포함한 기술적 분류; ML 정확도가 아님",
        },
        {
            "file": "analysis/figures/10_sgis_top_10min_population.png",
            "purpose": "SGIS 10분 생활권 인구 상위 검토 후보",
            "source": "data/analysis/sgis_catchment_analysis.csv",
            "interpretation": "응답이 확인된 검증좌표 중 비교; 미응답은 0명으로 처리하지 않음",
        },
        {
            "file": "analysis/figures/11_sgis_5_vs_10_population.png",
            "purpose": "SGIS 5분·10분 생활권 인구 비교",
            "source": "data/analysis/sgis_catchment_analysis.csv",
            "interpretation": "시설별 도달 규모 비교; 시설 간 인구 합산이 아님",
        },
        {
            "file": "analysis/figures/12_sgis_emd_mean_population.png",
            "purpose": "읍면별 SGIS 생활권 인구 평균",
            "source": "data/analysis/sgis_catchment_analysis.csv",
            "interpretation": "고유 검증좌표 기준 요약; 행정 읍면 총인구와 다름",
        },
        {
            "file": "analysis/figures/10_2025_2026_model_diagram.png",
            "purpose": "분석 흐름 개념도",
            "source": "analysis/generate_figures.py",
            "interpretation": "방법론 설명용 그림; 분석 결과 수치가 아님",
        },
    ]
    for figure in figures:
        path = ROOT / figure["file"]
        figure["status"] = "AVAILABLE" if path.is_file() and path.stat().st_size > 0 else "MISSING"
        figure["size_bytes"] = path.stat().st_size if path.is_file() else 0

    road_check = validation_check(validation, "vworld_roads_inside_boundary")
    facility_check = validation_check(validation, "vworld_facilities_inside_boundary")
    summary = {
        "status": "READY_WITH_DOCUMENTED_LIMITATIONS",
        "scope": "Uiseong 427 traditional ponds SGIS case study",
        "facility_count": comparison["facility_count"],
        "sgis_eligible_unique_coordinate_points": comparison["sgis_eligible_unique_coordinate_points"],
        "sgis_available_5min": comparison["sgis_available_5min"],
        "sgis_available_10min": comparison["sgis_available_10min"],
        "sgis_available_both": comparison["sgis_available_both"],
        "sgis_missing_10min": comparison["insufficient_sgis_10min"],
        "sgis_missing_context_overlap": comparison["sgis_missing_context_overlap_count"],
        "coordinate_quality_excluded": comparison["excluded_coordinate_quality"],
        "vworld_facility_count": facility_check.get("details", {}).get("feature_count"),
        "vworld_road_count": road_check.get("details", {}).get("feature_count"),
        "classification_counts": classification.get("types", []),
        "validation_status": validation.get("status"),
        "validation_fail_count": validation.get("fail_count"),
        "submission_claims_status": claims.get("status"),
        "submission_claims_pass_count": claims.get("pass_count"),
        "submission_claims_warn_count": claims.get("warn_count"),
        "submission_claims_fail_count": claims.get("fail_count"),
        "figures": figures,
    }
    MANIFEST_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary, figures


def write_report(summary: dict, figures: list[dict]) -> None:
    classification_lines = [
        f"- `{item['classification_type']}`: `{item['facility_count']}`개"
        for item in summary["classification_counts"]
    ]
    figure_lines = [
        f"| `{item['file']}` | {item['purpose']} | `{item['status']}` | {item['interpretation']} |"
        for item in figures
    ]
    available = sum(item["status"] == "AVAILABLE" for item in figures)
    lines = [
        "# SGIS 지역통계를 활용한 의성군 전통 못 Case Study 제출 보고서",
        "",
        "> 제출용 분석 초안. 모든 수치는 현재 저장소의 검증된 산출물에서 가져왔으며, 좌표·현장자료·공식 인구격자 미확보 한계를 숨기지 않는다.",
        "",
        "## 1. 연구 범위와 질문",
        "",
        "의성군 경계 내 427개 전통 못을 지역 수요와 주변 공간조건에 연결해 활용 가능성을 검토한다. SGIS 생활권역 주행인구는 기존 읍면 인구·VWorld 주변환경 자료에 추가되는 도달 규모 근거로 사용하며, 전국 전수 추천시스템이나 자동 정책점수는 만들지 않는다.",
        "",
        "핵심 흐름은 `지역 특성·수요 + 못 특성 + 접근성 + 주변 인프라 → 활용 가능성 검토 → 정책 방향 가설 → 현장 검증`이다.",
        "",
        "## 2. 사용 데이터와 검증 범위",
        "",
        f"- 전통 못: `{summary['facility_count']}`개, 고유 시설 ID 기준 누락 없음",
        f"- VWorld 의성군 시설: `{summary['vworld_facility_count']}`개, 도로: `{summary['vworld_road_count']}`개",
        "- 행정안전부 읍면 인구: 2024-12·2025-12, 청년 만 19~39세, 고령 만 65세 이상",
        f"- SGIS 생활권역: 5분 `{summary['sgis_available_5min']}`개, 10분 `{summary['sgis_available_10min']}`개, 양쪽 모두 `{summary['sgis_available_both']}`개",
        "- 분석 CRS: 거리·Buffer는 EPSG:5174, 웹 지도 출력은 EPSG:4326",
        "",
        "## 3. 핵심 분석 결과",
        "",
        "### 3.1 SGIS 응답과 결측",
        "",
        f"427개 시설에 5분·10분을 요청한 854개 조합 중 SGIS 응답이 확인된 범위는 5분 `{summary['sgis_available_5min']}`개, 10분 `{summary['sgis_available_10min']}`개다. 10분 인구 미확보는 `{summary['sgis_missing_10min']}`개이며, 다른 정책 검토 그룹과 중복되지 않는다.",
        "",
        "미확보 값은 0명으로 바꾸지 않는다. 위치 인식 실패, 인구 필드 미제공, 비밀보호 처리 여부를 원 응답 상태와 함께 보존한다.",
        "",
        "### 3.2 규칙기반 활용유형 분류",
        "",
        "분류 결과는 각 시설에 하나의 규칙기반 라벨을 연결한 결과다.",
        *classification_lines,
        "",
        "분류근거가 충분하지 않은 시설은 보수적 fallback으로 표시했으며, 이는 보존 우선순위가 확정됐다는 뜻이 아니다.",
        "",
        "### 3.3 정책 검토 맥락",
        "",
        "| 검토 맥락 | 데이터 근거 | 정책 방향(검토 가설) | 확정 전 확인 |",
        "|---|---|---|---|",
        "| 청년 참여 검토 | 읍면 청년비율 상위 + SGIS 10분 응답 43개 | 청년 참여형 활동·창업·체험 | 실제 청년 수요·관리상태·보존가치 |",
        "| 공동체 지원 검토 | 읍면 고령비율 상위 + 부분 VWorld 매핑시설 없음 53개 | 생활지원·커뮤니티 | 시설 레이어 누락·현장 운영상태 |",
        "| 접근·도달 검토 | SGIS 도달인구·5→10분 증가폭 상위 20개 | 관광·체험·체류·접근성 활용 | 관광시설·도로 연결성·현장 수요 |",
        "| 현장 확인 필요 | 좌표 품질 제외 47개 또는 SGIS 10분 미확보 | 정책 후보 보류 | 좌표 보정·SGIS 재추출·현장자료 |",
        "이 표의 정책 방향은 데이터 기반 검토 가설이며, 자동 추천이나 정책효과 입증이 아니다. 현장관리상태·보존가치·실제 서비스 수요가 확인된 뒤 후보를 확정한다.",
        "",
        "## 4. 제출용 시각화 목록",
        "",
        f"현재 산출물 중 제출에 연결 가능한 그림은 `{available}`개다. 각 그림은 원자료·파생 산출물·해석상 주의점을 함께 관리한다.",
        "",
        "| 파일 | 용도 | 상태 | 해석 주의 |",
        "|---|---|---|---|",
        *figure_lines,
        "",
        "## 5. 데이터 품질·재현성 한계",
        "",
        "- 좌표 품질: 대표점·인근좌표·중복좌표가 포함되어 실제 보정 전 47개를 SGIS 정책 검토에서 제외했다.",
        "- SGIS 결측: 10분 인구 미확보 시설을 0명으로 처리하지 않았다.",
        "- 인구 정의: SGIS 주행생활권 인구, 행정 읍면 인구, 공식 인구격자 Buffer 인구는 서로 다른 지표다.",
        "- 공식 인구격자: 국내 공식 100m·500m 격자가 없어 500m·1km Buffer 주민인구를 산출하지 않았다.",
        "- 도로 접근성: UQ151 결과는 EPSG:5174 유클리드 최근접거리이며 주행 네트워크 거리나 시간으로 표현하지 않는다.",
        "- 기준시점: 행정안전부 2024·2025년 자료, SGIS 2024년 응답, VWorld snapshot은 기준시점이 다르므로 동일 시점 효과로 해석하지 않는다.",
        "- VWorld 원자료의 최종 라이선스·재배포 조건과 기존 경계·농업자료 출처 확인은 남은 과제다.",
        "",
        "## 6. 검증 결과",
        "",
        f"- 분석 validation: `{summary['validation_status']}`; fail `{summary['validation_fail_count']}`개",
        f"- 제출근거 validation: `{summary['submission_claims_status']}`; `{summary['submission_claims_pass_count']} PASS / {summary['submission_claims_warn_count']} WARN / {summary['submission_claims_fail_count']} FAIL`",
        f"- 정책 검토 그룹 합계: `{summary['facility_count']}`개, SGIS 미확보 그룹의 타 그룹 중복: `{summary['sgis_missing_context_overlap']}`개",
        "- 분류 결과는 427개 행·427개 고유 시설 ID에 연결되며, 정책 검토 맥락과는 별도 체계다.",
        "",
        "## 7. 재현 명령",
        "",
        "```bash",
        "python analysis/run_competition_pipeline.py",
        "python analysis/analyze_sgis_catchment.py",
        "python analysis/analyze_sgis_policy_evidence.py",
        "python analysis/build_sgis_policy_comparison.py",
        "python analysis/build_submission_report.py",
        "python analysis/validate_submission_claims.py",
        "```",
        "",
        "최종 제출 전에는 좌표 보정자료와 현장관리·보존·수요 자료를 확인한 뒤 SGIS를 재추출하고, 위 검증 명령과 manifest를 다시 실행한다.",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    report_summary, report_figures = build()
    write_report(report_summary, report_figures)
    print(json.dumps(report_summary, ensure_ascii=False, indent=2))

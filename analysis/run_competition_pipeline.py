"""공모전용 공간분석 재현 실행기."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from prepare_population import prepare
from prepare_vworld import prepare as prepare_vworld
from population_analysis import run as run_population
from accessibility_analysis import run as run_accessibility
from pond_context_analysis import run as run_context
from worldpop_reference_analysis import run as run_worldpop_reference
from traffic_culture_analysis import run as run_traffic_culture
from classify_ponds import run as run_classification
from policy_priority_scenarios import run as run_policy_priority
from build_competition_outputs import run as build_outputs
from generate_figures import run as generate_figures
from build_source_manifest import run as build_source_manifest
from validate_outputs import run as validate_outputs
from validate_submission_claims import run as validate_submission_claims


def main() -> None:
    print("[1/10] population preparation")
    prepare()
    print("[2/10] VWorld layer preparation")
    prepare_vworld()
    print("[3/10] population analysis")
    run_population()
    print("[4/10] accessibility analysis")
    run_accessibility()
    print("[5/10] context/buffer analysis")
    run_context()
    worldpop = run_worldpop_reference()
    print(f"WorldPop reference buffer: {worldpop['status']}")
    print("[6/10] traffic/culture context")
    run_traffic_culture()
    print("[7/10] rule-based classification")
    run_classification()
    priority = run_policy_priority()
    print(f"policy priority scenarios: {priority['status']}")
    print("[8/10] competition outputs")
    build_outputs()
    print("[9/10] figures")
    generate_figures()
    print("[9b] source manifest")
    manifest = build_source_manifest()
    print(f"source manifest: {manifest['status']} ({manifest['record_count']} records)")
    print("[10/11] validation")
    report = validate_outputs()
    print(f"validation: {report['status']}")
    print("[11/11] submission claim validation")
    claims = validate_submission_claims()
    print(f"submission claims: {claims['status']}")
    passed = all(item["status"] == "PASS" for item in (manifest, report, claims))
    print(f"pipeline complete: {'PASS' if passed else 'FAIL'}")


if __name__ == "__main__":
    main()

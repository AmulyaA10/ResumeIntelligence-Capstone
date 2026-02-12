"""
Integration test runner for JD-resume matching with expectations.json.

Usage:
  python3 tests/integration_runner.py

Requires LLM env vars:
  LLM_PROVIDER, LLM_API_KEY, LLM_MODEL (optional)
"""

import json
import sys
from pathlib import Path

from services.matching_workflow import match_resumes_to_jd
from services.resume_parser import extract_text
from tests.conftest import configure_llm_from_env


PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXPECTATIONS_PATH = PROJECT_ROOT / "data" / "expected_results" / "expectations.json"
RESUME_DIR = PROJECT_ROOT / "data" / "test_resumes"
JD_DIR = PROJECT_ROOT / "data" / "test_jds"


def load_expectations():
    with open(EXPECTATIONS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def scenario_resume_texts(resume_files):
    resume_texts = []
    for name in resume_files:
        path = RESUME_DIR / name
        resume_texts.append(extract_text(str(path)))
    return resume_texts


def run_scenario(scenario):
    jd_path = JD_DIR / scenario["jd_file"]
    jd_text = extract_text(str(jd_path))

    resume_files = scenario["resume_files"]
    resume_texts = scenario_resume_texts(resume_files)

    # Map resume text -> filename for identification
    text_to_name = {text: name for text, name in zip(resume_texts, resume_files)}

    result = match_resumes_to_jd(jd_text, resume_texts)
    ranked = result["ranked_candidates"]

    ranked_names = []
    for candidate in ranked:
        name = text_to_name.get(candidate["resume_text"], "UNKNOWN")
        ranked_names.append(name)

    top_k = scenario.get("top_k", 1)
    bottom_k = scenario.get("bottom_k", 1)

    expected_top = set(scenario.get("expected_top", []))
    expected_bottom = set(scenario.get("expected_bottom", []))

    top_slice = set(ranked_names[:top_k])
    bottom_slice = set(ranked_names[-bottom_k:]) if bottom_k > 0 else set()

    failures = []

    for name in expected_top:
        if name not in top_slice:
            failures.append(f"Expected top candidate missing from top {top_k}: {name}")

    for name in expected_bottom:
        if name not in bottom_slice:
            failures.append(f"Expected bottom candidate missing from bottom {bottom_k}: {name}")

    return ranked_names, failures


def main():
    if not configure_llm_from_env():
        print("LLM not configured. Set LLM_PROVIDER and LLM_API_KEY (and optionally LLM_MODEL).")
        return 2

    expectations = load_expectations()
    scenarios = expectations.get("scenarios", [])

    total_failures = 0

    for scenario in scenarios:
        name = scenario.get("name", "unnamed")
        print("=" * 80)
        print(f"Scenario: {name}")
        print("=" * 80)

        ranked_names, failures = run_scenario(scenario)

        print("Ranked order:")
        for idx, fname in enumerate(ranked_names, start=1):
            print(f"  {idx}. {fname}")

        if failures:
            total_failures += len(failures)
            print("\nFailures:")
            for f in failures:
                print(f"  - {f}")
        else:
            print("\nAll expectations satisfied.")

        print()

    if total_failures > 0:
        print(f"FAILED: {total_failures} expectation(s) not met.")
        return 1

    print("PASSED: All scenarios met expectations.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

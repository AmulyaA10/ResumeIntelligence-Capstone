"""
Unit tests for risk_detector.py — NO LLM required.

Run: python3 -m pytest tests/test_risk_detector.py -v
"""

import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.risk_detector import (
    detect_risk_flags,
    get_penalty_score,
    CURRENT_YEAR,
)


class TestRiskDetector:
    def test_no_flags_for_strong_resume(self, make_resume_signals, devops_jd):
        signals = make_resume_signals(
            skills=[
                {"skill": "aws", "context": "Built and deployed production systems on AWS with Terraform and Lambda"},
                {"skill": "docker", "context": "Designed container strategy and optimized image sizes in CI/CD"},
                {"skill": "kubernetes", "context": "Managed EKS clusters, upgraded versions, and tuned autoscaling"},
            ],
            projects=[{"name": "Proj", "description": "D", "impact": "I"}],
            measurable_outcomes=["Reduced cost by 20%", "Improved uptime to 99.9%"],
            has_recent_experience=True,
            most_recent_role_year=CURRENT_YEAR,
            domain_experience=["saas", "cloud infrastructure"],
            total_years=7,
        )
        risks = detect_risk_flags(signals, devops_jd).to_dict()
        assert risks["total_penalty"] == 0
        assert risks["flags"] == []

    def test_weak_evidence_skills_without_context(self, make_resume_signals, devops_jd):
        signals = make_resume_signals(
            skills=[
                {"skill": "aws", "context": "Used"},
                {"skill": "docker", "context": "Worked on"},
                {"skill": "kubernetes", "context": "Did things"},
                {"skill": "python", "context": "Scripts"},
            ],
            projects=[{"name": "Proj", "description": "D", "impact": "I"}],
            measurable_outcomes=["Reduced cost by 20%"],
            most_recent_role_year=CURRENT_YEAR,
        )
        risks = detect_risk_flags(signals, devops_jd).to_dict()
        categories = {f["category"] for f in risks["flags"]}
        assert "WEAK_EVIDENCE" in categories

    def test_no_quantification_and_low_quantification(self, make_resume_signals, devops_jd):
        signals_none = make_resume_signals(measurable_outcomes=[])
        risks_none = detect_risk_flags(signals_none, devops_jd).to_dict()
        categories_none = {f["category"] for f in risks_none["flags"]}
        assert "NO_QUANTIFICATION" in categories_none

        signals_low = make_resume_signals(measurable_outcomes=["Saved $10K"])
        risks_low = detect_risk_flags(signals_low, devops_jd).to_dict()
        categories_low = {f["category"] for f in risks_low["flags"]}
        assert "LOW_QUANTIFICATION" in categories_low

    def test_buzzword_flags(self, make_resume_signals, devops_jd):
        signals_moderate = make_resume_signals(
            skills=[
                {"skill": "aws", "context": "Built systems"},
            ]
        )
        signals_moderate["summary"] = "Results-oriented team player and self-starter."
        risks_moderate = detect_risk_flags(signals_moderate, devops_jd).to_dict()
        categories_moderate = {f["category"] for f in risks_moderate["flags"]}
        assert "BUZZWORD_MODERATE" in categories_moderate

        signals_heavy = make_resume_signals()
        signals_heavy["summary"] = (
            "Strategic results-oriented team player and self-starter with proven track record. "
            "Dynamic thought leader."
        )
        risks_heavy = detect_risk_flags(signals_heavy, devops_jd).to_dict()
        categories_heavy = {f["category"] for f in risks_heavy["flags"]}
        assert "BUZZWORD_HEAVY" in categories_heavy

    def test_outdated_experience_flag(self, make_resume_signals, devops_jd):
        signals = make_resume_signals(
            has_recent_experience=False,
            most_recent_role_year=CURRENT_YEAR - 3,
        )
        risks = detect_risk_flags(signals, devops_jd).to_dict()
        categories = {f["category"] for f in risks["flags"]}
        assert "OUTDATED_EXPERIENCE" in categories

    def test_no_projects_flag(self, make_resume_signals, devops_jd):
        signals = make_resume_signals(projects=[])
        risks = detect_risk_flags(signals, devops_jd).to_dict()
        categories = {f["category"] for f in risks["flags"]}
        assert "NO_PROJECTS" in categories

    def test_domain_mismatch_flag(self, make_resume_signals, devops_jd):
        signals = make_resume_signals(domain_experience=["fintech", "healthcare"])
        risks = detect_risk_flags(signals, devops_jd).to_dict()
        categories = {f["category"] for f in risks["flags"]}
        assert "DOMAIN_MISMATCH" in categories

    def test_no_domain_mismatch_if_resume_has_no_domains(self, make_resume_signals, devops_jd):
        signals = make_resume_signals(domain_experience=[])
        risks = detect_risk_flags(signals, devops_jd).to_dict()
        categories = {f["category"] for f in risks["flags"]}
        assert "DOMAIN_MISMATCH" not in categories

    def test_experience_gap_flag(self, make_resume_signals, devops_jd):
        signals = make_resume_signals(total_years=2)
        risks = detect_risk_flags(signals, devops_jd).to_dict()
        categories = {f["category"] for f in risks["flags"]}
        assert "EXPERIENCE_GAP" in categories

    def test_penalty_is_capped_at_20(self, make_resume_signals, devops_jd):
        signals = make_resume_signals(
            skills=[
                {"skill": "aws", "context": "Used"},
                {"skill": "docker", "context": "Used"},
                {"skill": "kubernetes", "context": "Used"},
            ],
            measurable_outcomes=[],
            projects=[],
            has_recent_experience=False,
            most_recent_role_year=CURRENT_YEAR - 5,
            domain_experience=["fintech"],
            total_years=1,
        )
        risks = detect_risk_flags(signals, devops_jd).to_dict()
        assert risks["total_penalty"] <= 20

    def test_get_penalty_score_matches_detect(self, make_resume_signals, devops_jd):
        signals = make_resume_signals(
            measurable_outcomes=[],
            projects=[],
            has_recent_experience=False,
            most_recent_role_year=CURRENT_YEAR - 5,
        )
        penalty_via_getter = get_penalty_score(signals, devops_jd)
        penalty_via_detect = detect_risk_flags(signals, devops_jd).to_dict()["total_penalty"]
        assert penalty_via_getter == penalty_via_detect

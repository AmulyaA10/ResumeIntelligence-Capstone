"""
Unit tests for scoring_engine.py — NO LLM required.
Tests each scoring dimension with hand-crafted mock signal dicts.

Run: python3 -m pytest tests/test_scoring_engine.py -v
"""

import sys
from pathlib import Path
from datetime import datetime

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.scoring_engine import (
    calculate_skill_coverage_score,
    calculate_experience_depth_score,
    calculate_domain_relevance_score,
    calculate_evidence_quality_score,
    calculate_quantification_score,
    calculate_recency_score,
    calculate_total_score,
    CURRENT_YEAR,
)


# ===================================================================
# Skill Coverage (0-30 points)
# ===================================================================
class TestSkillCoverage:
    """3 pts per matched must-have skill + 0.5 bonus for context > 30 chars."""

    def test_zero_skills_matched(self, make_resume_signals, devops_jd):
        signals = make_resume_signals(skills=[
            {"skill": "java", "context": "Built microservices in Java"},
            {"skill": "c++", "context": "Systems programming"},
        ])
        result = calculate_skill_coverage_score(signals, devops_jd)
        assert result["score"] == 0
        assert len(result["matched_skills"]) == 0
        assert len(result["missing_skills"]) == 10

    def test_five_of_ten_matched_no_context(self, make_resume_signals, devops_jd):
        signals = make_resume_signals(skills=[
            {"skill": "aws", "context": "Used AWS"},
            {"skill": "docker", "context": "Containers"},
            {"skill": "kubernetes", "context": "K8s"},
            {"skill": "python", "context": "Scripts"},
            {"skill": "linux", "context": "Servers"},
        ])
        result = calculate_skill_coverage_score(signals, devops_jd)
        # 5 * 3 = 15 base, no context bonus (all < 30 chars)
        assert result["score"] == 15
        assert len(result["matched_skills"]) == 5
        assert len(result["missing_skills"]) == 5

    def test_all_ten_matched_no_context(self, make_resume_signals, devops_jd):
        skills = [{"skill": s, "context": "Used"} for s in [
            "aws", "docker", "kubernetes", "ci/cd", "terraform",
            "python", "linux", "git", "monitoring", "agile"
        ]]
        signals = make_resume_signals(skills=skills)
        result = calculate_skill_coverage_score(signals, devops_jd)
        # 10 * 3 = 30, capped at 30
        assert result["score"] == 30

    def test_context_bonus_applied(self, make_resume_signals, devops_jd):
        skills = [
            {"skill": "aws", "context": "Deployed production workloads on AWS EC2, Lambda, and S3 buckets"},
            {"skill": "docker", "context": "Built Docker containerization strategy reducing image sizes by 40%"},
            {"skill": "python", "context": "Short"},  # < 30 chars, no bonus
        ]
        signals = make_resume_signals(skills=skills)
        result = calculate_skill_coverage_score(signals, devops_jd)
        # 3 skills matched * 3pts = 9 base
        # 2 skills with context > 30 chars * 0.5 = 1.0 bonus
        assert result["score"] == 10.0

    def test_partial_name_matching(self, make_resume_signals, devops_jd):
        """'aws' should match if resume has 'aws' in skill name."""
        signals = make_resume_signals(skills=[
            {"skill": "aws ec2", "context": "Managed EC2 instances"},
        ])
        result = calculate_skill_coverage_score(signals, devops_jd)
        # "aws" is in "aws ec2" — should match
        assert len(result["matched_skills"]) >= 1

    def test_score_capped_at_30(self, make_resume_signals, devops_jd):
        """Even with many context bonuses, score should not exceed 30."""
        skills = [
            {"skill": s, "context": f"Extensive production experience with {s} in large-scale systems"}
            for s in [
                "aws", "docker", "kubernetes", "ci/cd", "terraform",
                "python", "linux", "git", "monitoring", "agile"
            ]
        ]
        signals = make_resume_signals(skills=skills)
        result = calculate_skill_coverage_score(signals, devops_jd)
        # 10 * 3 = 30 base + 10 * 0.5 = 5 bonus = 35, but capped at 30
        assert result["score"] == 30


# ===================================================================
# Experience Depth (0-20 points)
# ===================================================================
class TestExperienceDepth:
    """10pts meets min, +2/extra yr (max 5), +2 seniority match."""

    def test_meets_minimum_exactly(self, make_resume_signals, devops_jd):
        signals = make_resume_signals(total_years=5, positions=[
            {"role": "DevOps Engineer", "company": "Co", "duration": "2020-2025", "years": 5}
        ])
        result = calculate_experience_depth_score(signals, devops_jd)
        # 10 base + 0 extra = 10
        assert result["score"] == 10

    def test_exceeds_by_3_years(self, make_resume_signals, devops_jd):
        signals = make_resume_signals(total_years=8, positions=[
            {"role": "DevOps Engineer", "company": "Co", "duration": "2017-2025", "years": 8}
        ])
        result = calculate_experience_depth_score(signals, devops_jd)
        # 10 base + 3*2 = 16
        assert result["score"] == 16

    def test_exceeds_capped_at_5_extra(self, make_resume_signals, devops_jd):
        signals = make_resume_signals(total_years=15, positions=[
            {"role": "DevOps Engineer", "company": "Co", "duration": "2010-2025", "years": 15}
        ])
        result = calculate_experience_depth_score(signals, devops_jd)
        # 10 base + 5*2 = 20, capped at 20
        assert result["score"] == 20

    def test_below_minimum_partial_credit(self, make_resume_signals, devops_jd):
        signals = make_resume_signals(total_years=2, positions=[
            {"role": "Junior DevOps", "company": "Co", "duration": "2023-2025", "years": 2}
        ])
        result = calculate_experience_depth_score(signals, devops_jd)
        # partial: (2/5) * 10 = 4.0
        assert result["score"] == 4.0

    def test_zero_experience(self, make_resume_signals, devops_jd):
        signals = make_resume_signals(total_years=0, positions=[])
        result = calculate_experience_depth_score(signals, devops_jd)
        assert result["score"] == 0

    def test_seniority_match_bonus(self, make_resume_signals, devops_jd):
        """Senior role title + Senior JD = +2 bonus."""
        signals = make_resume_signals(total_years=5, positions=[
            {"role": "Senior DevOps Engineer", "company": "Co", "duration": "2020-2025", "years": 5}
        ])
        result = calculate_experience_depth_score(signals, devops_jd)
        # 10 base + 0 extra + 2 seniority = 12
        assert result["score"] == 12

    def test_no_seniority_match(self, make_resume_signals, devops_jd):
        """Junior title applying to Senior JD — no seniority bonus."""
        signals = make_resume_signals(total_years=5, positions=[
            {"role": "Junior DevOps", "company": "Co", "duration": "2020-2025", "years": 5}
        ])
        result = calculate_experience_depth_score(signals, devops_jd)
        # 10 base + 0 extra + 0 seniority (junior != senior)
        assert result["score"] == 10


# ===================================================================
# Domain Relevance (0-15 points)
# ===================================================================
class TestDomainRelevance:
    """5 pts per matched domain keyword, max 3 matches = 15."""

    def test_zero_domain_match(self, make_resume_signals, devops_jd):
        signals = make_resume_signals(domain_experience=["healthcare", "biotech"])
        result = calculate_domain_relevance_score(signals, devops_jd)
        assert result["score"] == 0

    def test_one_domain_match(self, make_resume_signals, devops_jd):
        signals = make_resume_signals(domain_experience=["saas", "healthcare"])
        result = calculate_domain_relevance_score(signals, devops_jd)
        assert result["score"] == 5

    def test_two_domain_matches(self, make_resume_signals, devops_jd):
        signals = make_resume_signals(domain_experience=["saas", "cloud infrastructure"])
        result = calculate_domain_relevance_score(signals, devops_jd)
        assert result["score"] == 10

    def test_three_plus_capped(self, make_resume_signals, devops_jd):
        signals = make_resume_signals(
            domain_experience=["saas", "cloud infrastructure", "microservices", "devops"]
        )
        result = calculate_domain_relevance_score(signals, devops_jd)
        assert result["score"] == 15

    def test_empty_resume_domains(self, make_resume_signals, devops_jd):
        signals = make_resume_signals(domain_experience=[])
        result = calculate_domain_relevance_score(signals, devops_jd)
        assert result["score"] == 0


# ===================================================================
# Evidence Quality (0-15 points)
# ===================================================================
class TestEvidenceQuality:
    """Projects: 0→0, 1-2→5, 3+→8. Context rate: 80%→7, 50%→4, 30%→2."""

    def test_no_projects_no_skills(self, make_resume_signals):
        signals = make_resume_signals(projects=[], skills=[])
        result = calculate_evidence_quality_score(signals)
        assert result["score"] == 0

    def test_one_project_no_context(self, make_resume_signals):
        signals = make_resume_signals(
            projects=[{"name": "API", "description": "Built API", "impact": "Faster"}],
            skills=[{"skill": "python", "context": "Used"}],
        )
        result = calculate_evidence_quality_score(signals)
        # 5 for 1 project + 0 for context < 30 chars
        assert result["score"] == 5

    def test_three_projects(self, make_resume_signals):
        projects = [
            {"name": f"Project {i}", "description": "Desc", "impact": "Impact"}
            for i in range(3)
        ]
        signals = make_resume_signals(projects=projects, skills=[])
        result = calculate_evidence_quality_score(signals)
        # 8 for 3+ projects
        assert result["score"] == 8

    def test_context_rate_80_percent(self, make_resume_signals):
        """80%+ of skills have context > 30 chars → +7 points."""
        skills = [
            {"skill": f"skill_{i}", "context": f"Extensive production experience with skill_{i} in enterprise systems"}
            for i in range(8)
        ] + [
            {"skill": "other", "context": "Short"},  # 1 without, so 8/9 = 89%
            {"skill": "another", "context": "Also short"},  # 8/10 = 80%
        ]
        signals = make_resume_signals(projects=[], skills=skills)
        result = calculate_evidence_quality_score(signals)
        # 0 for projects + 7 for 80%+ context
        assert result["score"] == 7

    def test_context_rate_50_percent(self, make_resume_signals):
        """50-79% of skills have context > 30 chars → +4 points."""
        skills = [
            {"skill": "a", "context": "Very detailed context about production use of this skill"},
            {"skill": "b", "context": "Another very detailed context about this particular skill"},
            {"skill": "c", "context": "Short"},
            {"skill": "d", "context": "Also short"},
        ]
        # 2/4 = 50%
        signals = make_resume_signals(projects=[], skills=skills)
        result = calculate_evidence_quality_score(signals)
        assert result["score"] == 4

    def test_max_evidence_score(self, make_resume_signals):
        """3+ projects + 80%+ context = 8 + 7 = 15 (max)."""
        projects = [
            {"name": f"P{i}", "description": "D", "impact": "I"} for i in range(4)
        ]
        skills = [
            {"skill": f"s{i}", "context": f"Extensive production experience with s{i} in large-scale systems"}
            for i in range(10)
        ]
        signals = make_resume_signals(projects=projects, skills=skills)
        result = calculate_evidence_quality_score(signals)
        assert result["score"] == 15


# ===================================================================
# Quantification (0-10 points)
# ===================================================================
class TestQuantification:
    """0→0, 1-2→5, 3-4→8, 5+→10."""

    def test_zero_outcomes(self, make_resume_signals):
        signals = make_resume_signals(measurable_outcomes=[])
        result = calculate_quantification_score(signals)
        assert result["score"] == 0

    def test_one_outcome(self, make_resume_signals):
        signals = make_resume_signals(measurable_outcomes=["Reduced latency by 40%"])
        result = calculate_quantification_score(signals)
        assert result["score"] == 5

    def test_two_outcomes(self, make_resume_signals):
        signals = make_resume_signals(measurable_outcomes=[
            "Reduced latency by 40%", "Saved $50K annually"
        ])
        result = calculate_quantification_score(signals)
        assert result["score"] == 5

    def test_three_outcomes(self, make_resume_signals):
        signals = make_resume_signals(measurable_outcomes=[
            "Reduced latency by 40%", "Saved $50K", "Scaled to 10M users"
        ])
        result = calculate_quantification_score(signals)
        assert result["score"] == 8

    def test_four_outcomes(self, make_resume_signals):
        signals = make_resume_signals(measurable_outcomes=[
            "A", "B", "C", "D"
        ])
        result = calculate_quantification_score(signals)
        assert result["score"] == 8

    def test_five_plus_outcomes(self, make_resume_signals):
        signals = make_resume_signals(measurable_outcomes=[
            "A", "B", "C", "D", "E", "F"
        ])
        result = calculate_quantification_score(signals)
        assert result["score"] == 10


# ===================================================================
# Recency (0-10 points)
# ===================================================================
class TestRecency:
    """current_year-1→10, -2→7, -4→4, older→0."""

    def test_current_year(self, make_resume_signals):
        signals = make_resume_signals(most_recent_role_year=CURRENT_YEAR)
        result = calculate_recency_score(signals)
        assert result["score"] == 10

    def test_one_year_ago(self, make_resume_signals):
        signals = make_resume_signals(most_recent_role_year=CURRENT_YEAR - 1)
        result = calculate_recency_score(signals)
        assert result["score"] == 10

    def test_two_years_ago(self, make_resume_signals):
        signals = make_resume_signals(most_recent_role_year=CURRENT_YEAR - 2)
        result = calculate_recency_score(signals)
        assert result["score"] == 7

    def test_four_years_ago(self, make_resume_signals):
        signals = make_resume_signals(most_recent_role_year=CURRENT_YEAR - 4)
        result = calculate_recency_score(signals)
        assert result["score"] == 4

    def test_six_years_ago(self, make_resume_signals):
        signals = make_resume_signals(most_recent_role_year=CURRENT_YEAR - 6)
        result = calculate_recency_score(signals)
        assert result["score"] == 0

    def test_zero_year(self, make_resume_signals):
        signals = make_resume_signals(most_recent_role_year=0)
        result = calculate_recency_score(signals)
        assert result["score"] == 0


# ===================================================================
# Total Score (combines all + penalty)
# ===================================================================
class TestTotalScore:
    """Verifies the full scoring pipeline with mock risk flags."""

    def test_perfect_score_no_penalty(self, make_resume_signals, devops_jd):
        skills = [
            {"skill": s, "context": f"Extensive production experience with {s} in large-scale systems"}
            for s in [
                "aws", "docker", "kubernetes", "ci/cd", "terraform",
                "python", "linux", "git", "monitoring", "agile"
            ]
        ]
        signals = make_resume_signals(
            skills=skills,
            total_years=8,
            positions=[{"role": "Senior DevOps Engineer", "company": "Co", "duration": "2017-2025", "years": 8}],
            projects=[{"name": f"P{i}", "description": "D", "impact": "I"} for i in range(4)],
            measurable_outcomes=["A", "B", "C", "D", "E"],
            most_recent_role_year=CURRENT_YEAR,
            domain_experience=["saas", "cloud infrastructure", "microservices"],
        )
        risk_flags = {"flags": [], "total_penalty": 0}
        result = calculate_total_score(signals, devops_jd, risk_flags)

        assert result["final_score"] >= 90
        assert result["penalty"] == 0

    def test_penalty_subtracted(self, make_resume_signals, devops_jd):
        signals = make_resume_signals(
            skills=[{"skill": "aws", "context": "Used AWS for cloud deployments and infrastructure management"}],
            total_years=5,
            positions=[{"role": "Engineer", "company": "Co", "duration": "2020-2025", "years": 5}],
            most_recent_role_year=CURRENT_YEAR,
        )
        risk_flags = {"flags": [{"category": "TEST", "penalty": 10}], "total_penalty": 10}
        result = calculate_total_score(signals, devops_jd, risk_flags)

        assert result["penalty"] == 10
        assert result["final_score"] == result["base_score"] - 10

    def test_score_never_below_zero(self, make_resume_signals, devops_jd):
        signals = make_resume_signals(
            skills=[], total_years=0, positions=[], projects=[],
            measurable_outcomes=[], most_recent_role_year=0,
            domain_experience=[],
        )
        risk_flags = {"flags": [], "total_penalty": 20}
        result = calculate_total_score(signals, devops_jd, risk_flags)

        assert result["final_score"] >= 0

    def test_score_never_above_100(self, make_resume_signals, devops_jd):
        skills = [
            {"skill": s, "context": f"Extensive production experience with {s} in enterprise-scale systems"}
            for s in [
                "aws", "docker", "kubernetes", "ci/cd", "terraform",
                "python", "linux", "git", "monitoring", "agile"
            ]
        ]
        signals = make_resume_signals(
            skills=skills,
            total_years=20,
            positions=[{"role": "Senior Staff Engineer", "company": "Co", "duration": "2005-2025", "years": 20}],
            projects=[{"name": f"P{i}", "description": "D", "impact": "I"} for i in range(5)],
            measurable_outcomes=["A", "B", "C", "D", "E", "F", "G"],
            most_recent_role_year=CURRENT_YEAR,
            domain_experience=["saas", "cloud infrastructure", "microservices", "devops"],
        )
        risk_flags = {"flags": [], "total_penalty": 0}
        result = calculate_total_score(signals, devops_jd, risk_flags)

        assert result["final_score"] <= 100

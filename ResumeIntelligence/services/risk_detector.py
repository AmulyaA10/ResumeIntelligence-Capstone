"""
Risk Flag Detector - Guardrails Implementation
Detects vague claims, buzzwords, and weak evidence in resumes
"""

from typing import List, Dict
from datetime import datetime
import re

CURRENT_YEAR = datetime.now().year


# Buzzword list (common inflated terms without context)
BUZZWORDS = [
    "synergy", "leverage", "disrupt", "innovative", "strategic", "dynamic",
    "results-oriented", "team player", "hard worker", "detail-oriented",
    "self-starter", "go-getter", "thought leader", "rockstar", "ninja",
    "guru", "passionate", "motivated", "dedicated", "proven track record"
]

# Vague skill claims (skills without context indicators)
CONTEXT_INDICATORS = [
    "built", "developed", "deployed", "designed", "implemented", "created",
    "architected", "migrated", "optimized", "scaled", "reduced", "increased",
    "automated", "integrated", "led", "managed", "shipped", "launched"
]


class RiskFlags:
    """Container for detected risk flags"""

    def __init__(self):
        self.flags: List[Dict[str, str]] = []
        self.penalty_points: int = 0

    def add_flag(self, category: str, description: str, penalty: int = 2):
        """Add a risk flag with penalty points"""
        self.flags.append({
            "category": category,
            "description": description,
            "penalty": penalty
        })
        self.penalty_points += penalty

    def to_dict(self):
        return {
            "flags": self.flags,
            "total_penalty": min(self.penalty_points, 20)  # Cap at -20
        }


def detect_risk_flags(resume_signals: dict, jd_requirements: dict) -> RiskFlags:
    """
    Detect all risk flags in a resume based on extracted signals.

    Args:
        resume_signals: Output from resume_enricher.extract_resume_signals()
        jd_requirements: Output from jd_parser.parse_job_description()

    Returns:
        RiskFlags object with all detected issues
    """

    risks = RiskFlags()

    # 1. SKILLS WITHOUT CONTEXT
    skills_with_context = resume_signals.get("skills", [])
    skills_without_context = []

    for skill_item in skills_with_context:
        skill = skill_item.get("skill", "")
        context = skill_item.get("context", "").lower()

        # Check if context has action verbs (indicators of real usage)
        has_context = any(indicator in context for indicator in CONTEXT_INDICATORS)

        if not has_context or len(context) < 20:
            skills_without_context.append(skill)

    if len(skills_without_context) >= 3:
        risks.add_flag(
            "WEAK_EVIDENCE",
            f"{len(skills_without_context)} skills listed without project context: {', '.join(skills_without_context[:3])}",
            penalty=5
        )

    # 2. NO MEASURABLE OUTCOMES
    outcomes = resume_signals.get("measurable_outcomes", [])

    if len(outcomes) == 0:
        risks.add_flag(
            "NO_QUANTIFICATION",
            "No measurable outcomes or quantified achievements found (no %, $, numbers)",
            penalty=5
        )
    elif len(outcomes) < 2:
        risks.add_flag(
            "LOW_QUANTIFICATION",
            "Only 1 measurable outcome found; lacks evidence of impact",
            penalty=3
        )

    # 3. BUZZWORD OVERLOAD
    resume_text_lower = str(resume_signals).lower()
    buzzwords_found = [bw for bw in BUZZWORDS if bw in resume_text_lower]

    if len(buzzwords_found) >= 5:
        risks.add_flag(
            "BUZZWORD_HEAVY",
            f"Resume contains {len(buzzwords_found)} buzzwords without substance: {', '.join(buzzwords_found[:3])}...",
            penalty=4
        )
    elif len(buzzwords_found) >= 3:
        risks.add_flag(
            "BUZZWORD_MODERATE",
            f"Resume contains {len(buzzwords_found)} buzzwords: {', '.join(buzzwords_found)}",
            penalty=2
        )

    # 4. OUTDATED EXPERIENCE ONLY
    recency = resume_signals.get("recency_indicators", {})
    has_recent = recency.get("has_recent_experience", False)
    most_recent_year = recency.get("most_recent_role_year", 0)

    if not has_recent and most_recent_year > 0 and most_recent_year < CURRENT_YEAR - 2:
        risks.add_flag(
            "OUTDATED_EXPERIENCE",
            f"Most recent experience is from {most_recent_year}; no recent ({CURRENT_YEAR - 2}+) work shown",
            penalty=4
        )

    # 5. NO PROJECTS MENTIONED
    projects = resume_signals.get("projects", [])

    if len(projects) == 0:
        risks.add_flag(
            "NO_PROJECTS",
            "No specific projects mentioned; claims lack concrete examples",
            penalty=3
        )

    # 6. DOMAIN MISMATCH (if JD specifies domain)
    jd_domains = [d.lower() for d in jd_requirements.get("domain_keywords", [])]
    resume_domains = [d.lower() for d in resume_signals.get("domain_experience", [])]

    if jd_domains:
        domain_overlap = any(jd_d in resume_domains for jd_d in jd_domains)

        if not domain_overlap and len(resume_domains) > 0:
            risks.add_flag(
                "DOMAIN_MISMATCH",
                f"JD requires {', '.join(jd_domains[:2])} domain; resume shows {', '.join(resume_domains[:2])}",
                penalty=3
            )

    # 7. EXPERIENCE GAP (if JD requires min years)
    jd_min_years = jd_requirements.get("years_of_experience", {}).get("min", 0)
    resume_years = resume_signals.get("experience_duration", {}).get("total_years", 0)

    if jd_min_years > 0 and resume_years < jd_min_years:
        gap = jd_min_years - resume_years
        risks.add_flag(
            "EXPERIENCE_GAP",
            f"JD requires {jd_min_years}+ years; resume shows {resume_years} years (gap: {gap} years)",
            penalty=2
        )

    return risks


def get_penalty_score(resume_signals: dict, jd_requirements: dict) -> int:
    """
    Get total penalty points (0 to 20) for a resume.

    Args:
        resume_signals: Output from resume_enricher
        jd_requirements: Output from jd_parser

    Returns:
        Penalty points (0-20)
    """
    risks = detect_risk_flags(resume_signals, jd_requirements)
    return risks.to_dict()["total_penalty"]

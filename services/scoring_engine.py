"""
100-Point Scoring Engine
Rule-based, explainable scoring system.
"""

from typing import Dict, List
from datetime import datetime

CURRENT_YEAR = datetime.now().year


def calculate_skill_coverage_score(
    resume_signals: dict,
    jd_requirements: dict
) -> Dict:
    """
    Calculate skill coverage score (0-30 points).

    Scoring logic:
    - 3 points per matched must-have skill (10 skills max = 30 points)
    - Bonus: +0.5 points for skills with strong context

    Args:
        resume_signals: Output from resume_enricher
        jd_requirements: Output from jd_parser

    Returns:
        Dict with score, matched_skills, missing_skills, details
    """

    must_have_skills = [s.lower() for s in jd_requirements.get("must_have_skills", [])]
    resume_skills = resume_signals.get("skills", [])

    # Extract resume skill names (normalize to lowercase)
    resume_skill_names = [item.get("skill", "").lower() for item in resume_skills]

    # Find matches
    matched = []
    for jd_skill in must_have_skills:
        if any(jd_skill in rs for rs in resume_skill_names):
            matched.append(jd_skill)

    missing = [s for s in must_have_skills if s not in [m.lower() for m in matched]]

    # Base score: 3 points per match
    base_score = len(matched) * 3

    # Bonus: skills with strong context (> 30 chars)
    bonus = 0
    for skill_item in resume_skills:
        skill_name = skill_item.get("skill", "").lower()
        context = skill_item.get("context", "")

        if any(skill_name in m.lower() for m in matched) and len(context) > 30:
            bonus += 0.5

    total_score = min(base_score + bonus, 30)  # Cap at 30

    return {
        "score": round(total_score, 1),
        "max_score": 30,
        "matched_skills": matched,
        "missing_skills": missing,
        "match_rate": f"{len(matched)}/{len(must_have_skills)}",
        "details": f"Matched {len(matched)} of {len(must_have_skills)} required skills"
    }


def calculate_experience_depth_score(
    resume_signals: dict,
    jd_requirements: dict
) -> Dict:
    """
    Calculate experience depth score (0-20 points).

    Scoring logic:
    - Meet minimum years: 10 points
    - Exceed minimum: +2 points per extra year (max 5 extra = +10 points)
    - Relevant role titles: +2 points if matching seniority

    Args:
        resume_signals: Output from resume_enricher
        jd_requirements: Output from jd_parser

    Returns:
        Dict with score, years, details
    """

    jd_min_years = jd_requirements.get("years_of_experience", {}).get("min", 0)
    jd_seniority = jd_requirements.get("role_seniority", "").lower()

    resume_years = resume_signals.get("experience_duration", {}).get("total_years", 0)
    positions = resume_signals.get("experience_duration", {}).get("positions", [])

    score = 0

    # Base: Meet minimum years
    if resume_years >= jd_min_years:
        score += 10

        # Bonus: Extra years (2 points each, max 5 years)
        extra_years = min(resume_years - jd_min_years, 5)
        score += extra_years * 2

    elif resume_years > 0:
        # Partial credit if below minimum
        score += (resume_years / jd_min_years) * 10

    # Seniority match bonus
    if positions:
        recent_role = positions[0].get("role", "").lower()

        seniority_match = False
        if jd_seniority in ["senior", "lead", "principal"] and any(
            level in recent_role for level in ["senior", "lead", "principal", "staff"]
        ):
            seniority_match = True
        elif jd_seniority in ["mid", "intermediate"] and "engineer" in recent_role:
            seniority_match = True
        elif jd_seniority in ["junior", "entry"] and any(
            level in recent_role for level in ["junior", "associate", "engineer"]
        ):
            seniority_match = True

        if seniority_match:
            score += 2

    total_score = min(score, 20)

    return {
        "score": round(total_score, 1),
        "max_score": 20,
        "resume_years": resume_years,
        "required_years": jd_min_years,
        "details": f"{resume_years} years experience vs {jd_min_years} required"
    }


def calculate_domain_relevance_score(
    resume_signals: dict,
    jd_requirements: dict
) -> Dict:
    """
    Calculate domain relevance score (0-15 points).

    Scoring logic:
    - 5 points per matching domain keyword (max 3 matches = 15 points)

    Args:
        resume_signals: Output from resume_enricher
        jd_requirements: Output from jd_parser

    Returns:
        Dict with score, matched_domains, details
    """

    jd_domains = [d.lower() for d in jd_requirements.get("domain_keywords", [])]
    resume_domains = [d.lower() for d in resume_signals.get("domain_experience", [])]

    matched_domains = []
    for jd_domain in jd_domains:
        if any(jd_domain in rd for rd in resume_domains):
            matched_domains.append(jd_domain)

    # 5 points per match, max 3 matches
    score = min(len(matched_domains) * 5, 15)

    return {
        "score": score,
        "max_score": 15,
        "matched_domains": matched_domains,
        "required_domains": jd_domains[:3],
        "details": f"Matched {len(matched_domains)} of {len(jd_domains)} domain keywords"
    }


def calculate_evidence_quality_score(resume_signals: dict) -> Dict:
    """
    Calculate evidence quality score (0-15 points).

    Scoring logic:
    - Projects mentioned: 5 points (1+ projects), 8 points (3+ projects)
    - Skills with context: 7 points if 80%+ skills have context

    Args:
        resume_signals: Output from resume_enricher

    Returns:
        Dict with score, details
    """

    projects = resume_signals.get("projects", [])
    skills = resume_signals.get("skills", [])

    score = 0

    # Project evidence
    if len(projects) >= 3:
        score += 8
    elif len(projects) >= 1:
        score += 5

    # Skills with strong context (> 30 chars)
    if skills:
        skills_with_context = sum(1 for s in skills if len(s.get("context", "")) > 30)
        context_rate = skills_with_context / len(skills)

        if context_rate >= 0.8:
            score += 7
        elif context_rate >= 0.5:
            score += 4
        elif context_rate >= 0.3:
            score += 2

    return {
        "score": score,
        "max_score": 15,
        "projects_count": len(projects),
        "skills_with_context": sum(1 for s in skills if len(s.get("context", "")) > 30),
        "details": f"{len(projects)} projects mentioned, {sum(1 for s in skills if len(s.get('context', '')) > 30)}/{len(skills)} skills with context"
    }


def calculate_quantification_score(resume_signals: dict) -> Dict:
    """
    Calculate quantification/impact score (0-10 points).

    Scoring logic:
    - 0 outcomes: 0 points
    - 1-2 outcomes: 5 points
    - 3-4 outcomes: 8 points
    - 5+ outcomes: 10 points

    Args:
        resume_signals: Output from resume_enricher

    Returns:
        Dict with score, outcomes, details
    """

    outcomes = resume_signals.get("measurable_outcomes", [])
    count = len(outcomes)

    if count == 0:
        score = 0
    elif count <= 2:
        score = 5
    elif count <= 4:
        score = 8
    else:
        score = 10

    return {
        "score": score,
        "max_score": 10,
        "outcomes_count": count,
        "sample_outcomes": outcomes[:3],
        "details": f"{count} measurable outcomes found"
    }


def calculate_recency_score(resume_signals: dict) -> Dict:
    """
    Calculate recency score (0-10 points).

    Scoring logic:
    - Recent experience (2023+): 10 points
    - Recent experience (2022+): 7 points
    - Older (2020-2021): 4 points
    - Very old (<2020): 0 points

    Args:
        resume_signals: Output from resume_enricher

    Returns:
        Dict with score, most_recent_year, details
    """

    recency = resume_signals.get("recency_indicators", {})
    most_recent_year = recency.get("most_recent_role_year", 0)

    if most_recent_year >= CURRENT_YEAR - 1:
        score = 10
    elif most_recent_year >= CURRENT_YEAR - 2:
        score = 7
    elif most_recent_year >= CURRENT_YEAR - 4:
        score = 4
    else:
        score = 0

    return {
        "score": score,
        "max_score": 10,
        "most_recent_year": most_recent_year,
        "details": f"Most recent role: {most_recent_year}"
    }


def calculate_total_score(
    resume_signals: dict,
    jd_requirements: dict,
    risk_flags: dict
) -> Dict:
    """
    Calculate final 100-point score with all components.

    Args:
        resume_signals: Output from resume_enricher
        jd_requirements: Output from jd_parser
        risk_flags: Output from risk_detector

    Returns:
        Dict with all scores, breakdown, and final score (0-100)
    """

    skill_coverage = calculate_skill_coverage_score(resume_signals, jd_requirements)
    experience_depth = calculate_experience_depth_score(resume_signals, jd_requirements)
    domain_relevance = calculate_domain_relevance_score(resume_signals, jd_requirements)
    evidence_quality = calculate_evidence_quality_score(resume_signals)
    quantification = calculate_quantification_score(resume_signals)
    recency = calculate_recency_score(resume_signals)

    # Base score (0-100)
    base_score = (
        skill_coverage["score"] +
        experience_depth["score"] +
        domain_relevance["score"] +
        evidence_quality["score"] +
        quantification["score"] +
        recency["score"]
    )

    # Apply penalty (0 to -20)
    penalty = risk_flags.get("total_penalty", 0)

    # Final score (clamped to 0-100)
    final_score = max(0, min(100, base_score - penalty))

    return {
        "final_score": round(final_score, 1),
        "base_score": round(base_score, 1),
        "penalty": penalty,
        "breakdown": {
            "skill_coverage": skill_coverage,
            "experience_depth": experience_depth,
            "domain_relevance": domain_relevance,
            "evidence_quality": evidence_quality,
            "quantification": quantification,
            "recency": recency
        },
        "risk_flags": risk_flags
    }

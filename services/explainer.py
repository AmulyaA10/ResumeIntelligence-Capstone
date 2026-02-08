"""
Explainability Module - FR4 Implementation
Generates human-readable explanations and recommendations
"""

from typing import Dict, Literal


RecommendationType = Literal["Shortlist", "Review", "Reject"]


def generate_recommendation(final_score: float) -> RecommendationType:
    """
    Generate hiring recommendation based on final score.

    Thresholds:
    - >= 75: Shortlist (strong candidate)
    - 60-74: Review (potential fit, needs review)
    - < 60: Reject (poor fit)

    Args:
        final_score: Final score (0-100)

    Returns:
        One of: "Shortlist", "Review", "Reject"
    """

    if final_score >= 75:
        return "Shortlist"
    elif final_score >= 60:
        return "Review"
    else:
        return "Reject"


def explain_skill_coverage(skill_data: dict) -> str:
    """Generate explanation for skill coverage score"""

    matched = len(skill_data.get("matched_skills", []))
    missing = len(skill_data.get("missing_skills", []))
    score = skill_data.get("score", 0)

    explanation = f"**Skill Coverage: {score}/30 points**\n\n"

    if matched > 0:
        explanation += f"✅ **Matched Skills ({matched}):** {', '.join(skill_data['matched_skills'][:5])}"
        if matched > 5:
            explanation += f" (+{matched - 5} more)"
        explanation += "\n\n"

    if missing > 0:
        explanation += f"❌ **Missing Skills ({missing}):** {', '.join(skill_data['missing_skills'][:5])}"
        if missing > 5:
            explanation += f" (+{missing - 5} more)"
        explanation += "\n\n"

    return explanation


def explain_experience_depth(exp_data: dict) -> str:
    """Generate explanation for experience depth score"""

    score = exp_data.get("score", 0)
    resume_years = exp_data.get("resume_years", 0)
    required_years = exp_data.get("required_years", 0)

    explanation = f"**Experience Depth: {score}/20 points**\n\n"

    if resume_years >= required_years:
        explanation += f"✅ Has {resume_years} years of experience (requires {required_years}+ years)\n\n"
    else:
        explanation += f"⚠️ Has {resume_years} years of experience (requires {required_years}+ years) - **Gap: {required_years - resume_years} years**\n\n"

    return explanation


def explain_domain_relevance(domain_data: dict) -> str:
    """Generate explanation for domain relevance score"""

    score = domain_data.get("score", 0)
    matched = domain_data.get("matched_domains", [])
    required = domain_data.get("required_domains", [])

    explanation = f"**Domain Relevance: {score}/15 points**\n\n"

    if matched:
        explanation += f"✅ **Matching Domains:** {', '.join(matched)}\n\n"
    elif required:
        explanation += f"⚠️ **No domain match** - JD requires: {', '.join(required)}\n\n"
    else:
        explanation += "ℹ️ No specific domain requirements in JD\n\n"

    return explanation


def explain_evidence_quality(evidence_data: dict) -> str:
    """Generate explanation for evidence quality score"""

    score = evidence_data.get("score", 0)
    projects = evidence_data.get("projects_count", 0)
    skills_with_context = evidence_data.get("skills_with_context", 0)

    explanation = f"**Evidence Quality: {score}/15 points**\n\n"

    if projects >= 3:
        explanation += f"✅ Strong project evidence ({projects} projects mentioned)\n"
    elif projects >= 1:
        explanation += f"⚠️ Limited project evidence ({projects} project(s) mentioned)\n"
    else:
        explanation += "❌ No specific projects mentioned\n"

    explanation += f"ℹ️ {skills_with_context} skills have detailed context\n\n"

    return explanation


def explain_quantification(quant_data: dict) -> str:
    """Generate explanation for quantification score"""

    score = quant_data.get("score", 0)
    count = quant_data.get("outcomes_count", 0)
    samples = quant_data.get("sample_outcomes", [])

    explanation = f"**Quantified Impact: {score}/10 points**\n\n"

    if count > 0:
        explanation += f"✅ {count} measurable outcome(s) found:\n"
        for outcome in samples[:3]:
            explanation += f"  - {outcome}\n"
        explanation += "\n"
    else:
        explanation += "❌ No quantified achievements (no %, $, numbers, or metrics)\n\n"

    return explanation


def explain_recency(recency_data: dict) -> str:
    """Generate explanation for recency score"""

    score = recency_data.get("score", 0)
    most_recent_year = recency_data.get("most_recent_year", 0)

    explanation = f"**Recency: {score}/10 points**\n\n"

    if most_recent_year >= 2023:
        explanation += f"✅ Recent experience (most recent role: {most_recent_year})\n\n"
    elif most_recent_year >= 2022:
        explanation += f"⚠️ Moderately recent experience (most recent role: {most_recent_year})\n\n"
    elif most_recent_year >= 2020:
        explanation += f"⚠️ Somewhat dated experience (most recent role: {most_recent_year})\n\n"
    else:
        explanation += f"❌ Outdated experience (most recent role: {most_recent_year or 'unknown'})\n\n"

    return explanation


def explain_risk_flags(risk_data: dict) -> str:
    """Generate explanation for risk flags and penalties"""

    penalty = risk_data.get("total_penalty", 0)
    flags = risk_data.get("flags", [])

    if penalty == 0:
        return "**Risk Flags: None** ✅\n\nNo issues detected.\n\n"

    explanation = f"**Risk Flags: -{penalty} points** ⚠️\n\n"

    for flag in flags:
        category = flag.get("category", "")
        description = flag.get("description", "")
        flag_penalty = flag.get("penalty", 0)

        explanation += f"🚩 **{category}** (-{flag_penalty} pts): {description}\n\n"

    return explanation


def generate_full_explanation(score_result: dict) -> str:
    """
    Generate complete explanation for a candidate's score.

    Args:
        score_result: Output from scoring_engine.calculate_total_score()

    Returns:
        Markdown-formatted explanation string
    """

    final_score = score_result.get("final_score", 0)
    base_score = score_result.get("base_score", 0)
    penalty = score_result.get("penalty", 0)
    breakdown = score_result.get("breakdown", {})
    risk_flags = score_result.get("risk_flags", {})

    recommendation = generate_recommendation(final_score)

    # Header
    explanation = f"# Candidate Evaluation Report\n\n"
    explanation += f"## Final Score: {final_score}/100\n\n"

    # Recommendation badge
    if recommendation == "Shortlist":
        explanation += "### ✅ **RECOMMENDATION: SHORTLIST** (Strong Candidate)\n\n"
    elif recommendation == "Review":
        explanation += "### ⚠️ **RECOMMENDATION: REVIEW** (Potential Fit - Needs Further Review)\n\n"
    else:
        explanation += "### ❌ **RECOMMENDATION: REJECT** (Poor Fit)\n\n"

    explanation += f"**Base Score:** {base_score}/100 | **Penalty:** -{penalty} points\n\n"
    explanation += "---\n\n"

    # Score breakdown
    explanation += "## Score Breakdown\n\n"

    explanation += explain_skill_coverage(breakdown.get("skill_coverage", {}))
    explanation += explain_experience_depth(breakdown.get("experience_depth", {}))
    explanation += explain_domain_relevance(breakdown.get("domain_relevance", {}))
    explanation += explain_evidence_quality(breakdown.get("evidence_quality", {}))
    explanation += explain_quantification(breakdown.get("quantification", {}))
    explanation += explain_recency(breakdown.get("recency", {}))

    explanation += "---\n\n"

    # Risk flags
    explanation += explain_risk_flags(risk_flags)

    explanation += "---\n\n"

    # Summary
    explanation += "## Summary\n\n"

    if recommendation == "Shortlist":
        explanation += "This candidate demonstrates strong alignment with the job requirements. "
        explanation += "Proceed with next interview rounds.\n\n"
    elif recommendation == "Review":
        explanation += "This candidate shows potential but has some gaps or concerns. "
        explanation += "Review full resume and consider for phone screen to clarify fit.\n\n"
    else:
        explanation += "This candidate does not meet the minimum requirements or has significant red flags. "
        explanation += "Consider rejecting unless there are exceptional circumstances.\n\n"

    return explanation


def generate_summary_line(score_result: dict) -> str:
    """
    Generate one-line summary for candidate ranking tables.

    Args:
        score_result: Output from scoring_engine.calculate_total_score()

    Returns:
        Brief summary string
    """

    final_score = score_result.get("final_score", 0)
    breakdown = score_result.get("breakdown", {})

    matched = len(breakdown.get("skill_coverage", {}).get("matched_skills", []))
    missing = len(breakdown.get("skill_coverage", {}).get("missing_skills", []))

    return f"{matched}/{matched + missing} skills matched, {breakdown.get('experience_depth', {}).get('resume_years', 0)} years experience"

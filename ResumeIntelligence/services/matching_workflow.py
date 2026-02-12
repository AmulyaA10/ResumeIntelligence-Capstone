"""
JD-Resume Matching Workflow (LangGraph)
Orchestrates the complete JD-resume matching pipeline.
"""

from typing import TypedDict, List, Optional, Dict, Any
from langgraph.graph import StateGraph, END
from services.jd_parser import parse_job_description
from services.resume_enricher import extract_resume_signals
from services.risk_detector import detect_risk_flags
from services.scoring_engine import calculate_total_score
from services.explainer import generate_full_explanation, generate_recommendation, generate_summary_line
from services.db.lancedb_client import get_cached_signals


def validate_api_key():
    """
    Validate that an LLM API key is available via sidebar session state.

    Raises:
        ValueError: If no valid API key is found
    """
    try:
        import streamlit as st
        if st.session_state.get("llm_configured"):
            return True
    except Exception:
        pass

    raise ValueError(
        "No LLM configured. Please select a provider and enter your API key "
        "in the sidebar (⚙️ LLM Configuration)."
    )


class MatchingState(TypedDict):
    """State for JD-Resume matching workflow"""
    jd_text: str
    resume_texts: List[str]  # List of resume text strings
    jd_requirements: Optional[Dict]
    candidates: Optional[List[Dict[str, Any]]]  # List of candidate results
    ranked_candidates: Optional[List[Dict[str, Any]]]  # Sorted by score


def jd_parser_agent(state: MatchingState) -> Dict:
    """
    Agent 1: Parse job description and extract requirements.
    """
    jd_text = state["jd_text"]

    print("🔍 Parsing job description...")
    jd_requirements = parse_job_description(jd_text)

    return {"jd_requirements": jd_requirements}


def resume_batch_processor_agent(state: MatchingState) -> Dict:
    """
    Agent 2: Process all resumes and extract signals.
    Uses cached signals from LanceDB when available to skip LLM calls.
    """
    resume_texts = state["resume_texts"]
    jd_requirements = state["jd_requirements"]

    print(f"📄 Processing {len(resume_texts)} resumes...")

    candidates = []
    cache_hits = 0

    for idx, resume_text in enumerate(resume_texts):
        print(f"  Processing candidate {idx + 1}/{len(resume_texts)}...")

        # Check for cached signals first (skip LLM call if available)
        resume_signals = get_cached_signals(resume_text)
        if resume_signals:
            cache_hits += 1
            print(f"    ⚡ Using cached signals for candidate {idx + 1}")
        else:
            # Extract structured signals via LLM (no cache available)
            resume_signals = extract_resume_signals(resume_text)

        # Detect risk flags
        risk_flags = detect_risk_flags(resume_signals, jd_requirements)

        # Calculate score
        score_result = calculate_total_score(
            resume_signals,
            jd_requirements,
            risk_flags.to_dict()
        )

        # Generate explanation
        explanation = generate_full_explanation(score_result)

        # Generate recommendation
        recommendation = generate_recommendation(score_result["final_score"])

        # Generate summary
        summary = generate_summary_line(score_result)

        candidates.append({
            "candidate_id": f"Candidate_{idx + 1}",
            "resume_text": resume_text,
            "resume_signals": resume_signals,
            "score_result": score_result,
            "final_score": score_result["final_score"],
            "recommendation": recommendation,
            "explanation": explanation,
            "summary": summary
        })

    if cache_hits > 0:
        print(f"  ⚡ {cache_hits}/{len(resume_texts)} resumes used cached signals (skipped LLM)")

    return {"candidates": candidates}


def ranking_agent(state: MatchingState) -> Dict:
    """
    Agent 3: Rank candidates by score.
    """
    candidates = state["candidates"]

    print("📊 Ranking candidates...")

    # Sort by final_score (descending)
    ranked = sorted(candidates, key=lambda x: x["final_score"], reverse=True)

    # Add rank number
    for idx, candidate in enumerate(ranked):
        candidate["rank"] = idx + 1

    return {"ranked_candidates": ranked}


def build_matching_workflow() -> StateGraph:
    """
    Build the complete JD-Resume matching workflow.

    Workflow steps:
    1. Parse JD (extract requirements)
    2. Process all resumes (extract signals, detect risks, score)
    3. Rank candidates by score

    Returns:
        Compiled LangGraph workflow
    """

    graph = StateGraph(MatchingState)

    # Add nodes
    graph.add_node("jd_parser", jd_parser_agent)
    graph.add_node("resume_processor", resume_batch_processor_agent)
    graph.add_node("ranker", ranking_agent)

    # Define edges
    graph.set_entry_point("jd_parser")
    graph.add_edge("jd_parser", "resume_processor")
    graph.add_edge("resume_processor", "ranker")
    graph.add_edge("ranker", END)

    return graph.compile()


# Convenience function for direct usage
def match_resumes_to_jd(jd_text: str, resume_texts: List[str]) -> Dict:
    """
    Run the complete matching workflow.

    Args:
        jd_text: Job description text
        resume_texts: List of resume text strings

    Returns:
        Dict with ranked_candidates and jd_requirements

    Raises:
        ValueError: If API key is not configured
    """

    # Validate API key before processing
    validate_api_key()

    workflow = build_matching_workflow()

    result = workflow.invoke({
        "jd_text": jd_text,
        "resume_texts": resume_texts
    })

    return {
        "jd_requirements": result["jd_requirements"],
        "ranked_candidates": result["ranked_candidates"],
        "total_candidates": len(result["ranked_candidates"])
    }

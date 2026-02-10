"""
Enhanced Resume Parser - FR2 Implementation
Extracts structured signals from resumes for evidence-based scoring
"""

from typing import TypedDict, List, Optional, Dict
from langchain_core.prompts import PromptTemplate
from services.llm_config import get_llm
import json
import re

llm = get_llm(temperature=0)


class ResumeSignals(TypedDict):
    """Structured resume signals for scoring"""
    skills: List[Dict[str, str]]  # [{"skill": "Python", "context": "Built API using Python"}]
    experience_duration: dict  # {"total_years": 5, "recent_years": 2, "positions": [...]}
    projects: List[Dict[str, str]]  # [{"name": "...", "description": "...", "impact": "..."}]
    measurable_outcomes: List[str]  # ["Reduced latency by 40%", "Saved $50K annually"]
    recency_indicators: dict  # {"has_recent_experience": True, "most_recent_role_year": 2024}
    domain_experience: List[str]  # ["fintech", "healthcare"]
    education: Optional[str]
    certifications: List[str]


def extract_resume_signals(resume_text: str) -> ResumeSignals:
    """
    Extract all structured signals from resume for evidence-based scoring.

    Args:
        resume_text: Raw resume text

    Returns:
        ResumeSignals dict with all extracted fields
    """

    prompt = PromptTemplate(
        input_variables=["resume"],
        template="""
You are an expert resume analyzer extracting structured data for candidate evaluation.

Resume:
{resume}

TASK:
Extract ALL relevant signals with maximum detail. Be thorough and precise.

RULES:
1. skills: Extract skills WITH context/evidence. For each skill, include WHERE it was used.
   Example: {{"skill": "Python", "context": "Built REST APIs using Python/FastAPI for microservices"}}

2. experience_duration: Calculate total years, recent years (last 2 years), and list all positions with dates
   Example: {{
     "total_years": 5,
     "recent_years": 2,
     "positions": [
       {{"role": "Senior Engineer", "company": "ABC Corp", "duration": "2022-2024", "years": 2}},
       {{"role": "Engineer", "company": "XYZ Ltd", "duration": "2019-2022", "years": 3}}
     ]
   }}

3. projects: Extract specific projects with name, description, and impact/outcomes
   Example: {{"name": "Payment Gateway", "description": "Built microservices architecture", "impact": "Processed 1M transactions/day"}}

4. measurable_outcomes: Extract ONLY quantified achievements (numbers, %, $, scale, latency, users)
   Examples: ["Reduced deployment time by 60%", "Saved $100K annually", "Scaled to 10M users", "Decreased latency from 500ms to 50ms"]

5. recency_indicators: Determine if candidate has recent (2023-2024) experience
   Example: {{"has_recent_experience": true, "most_recent_role_year": 2024, "most_recent_role": "Senior Engineer at ABC Corp"}}

6. domain_experience: Extract industry domains worked in (e.g., "fintech", "healthcare", "e-commerce", "cloud infrastructure")

7. education: Extract degree(s) if mentioned

8. certifications: Extract any certifications

Return ONLY valid JSON (no markdown, no explanation):

{{
  "skills": [
    {{"skill": "Python", "context": "Built REST APIs using Python/FastAPI"}},
    {{"skill": "AWS", "context": "Deployed services on AWS ECS/Lambda"}}
  ],
  "experience_duration": {{
    "total_years": 5,
    "recent_years": 2,
    "positions": [
      {{"role": "Senior Engineer", "company": "ABC Corp", "duration": "2022-2024", "years": 2}}
    ]
  }},
  "projects": [
    {{"name": "Payment Gateway", "description": "Built microservices", "impact": "1M transactions/day"}}
  ],
  "measurable_outcomes": [
    "Reduced deployment time by 60%",
    "Saved $100K annually"
  ],
  "recency_indicators": {{
    "has_recent_experience": true,
    "most_recent_role_year": 2024,
    "most_recent_role": "Senior Engineer at ABC Corp"
  }},
  "domain_experience": ["fintech", "cloud infrastructure"],
  "education": "Bachelor's in Computer Science",
  "certifications": ["AWS Certified Solutions Architect"]
}}
"""
    )

    response = llm.invoke(prompt.format(resume=resume_text))

    try:
        parsed = json.loads(response.content)
        return parsed
    except json.JSONDecodeError:
        # Fallback to minimal structure
        return {
            "skills": [],
            "experience_duration": {"total_years": 0, "recent_years": 0, "positions": []},
            "projects": [],
            "measurable_outcomes": [],
            "recency_indicators": {"has_recent_experience": False, "most_recent_role_year": 0},
            "domain_experience": [],
            "education": None,
            "certifications": []
        }


def extract_years_of_experience(resume_text: str) -> float:
    """
    Quick extraction of total years of experience.

    Args:
        resume_text: Raw resume text

    Returns:
        Total years of experience (float)
    """
    signals = extract_resume_signals(resume_text)
    return signals["experience_duration"].get("total_years", 0)


def extract_skills_with_context(resume_text: str) -> List[Dict[str, str]]:
    """
    Extract skills with their usage context.

    Args:
        resume_text: Raw resume text

    Returns:
        List of dicts with skill and context
    """
    signals = extract_resume_signals(resume_text)
    return signals["skills"]


def has_quantified_impact(resume_text: str) -> bool:
    """
    Check if resume has measurable outcomes.

    Args:
        resume_text: Raw resume text

    Returns:
        True if resume contains quantified achievements
    """
    signals = extract_resume_signals(resume_text)
    return len(signals["measurable_outcomes"]) > 0

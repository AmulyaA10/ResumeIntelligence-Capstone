"""
JD Parser Module
Extracts structured requirements from job descriptions.
"""

from typing import TypedDict, List, Optional
from langchain_core.prompts import PromptTemplate
from services.llm_config import get_llm, extract_json
import json


class JDRequirements(TypedDict):
    """Structured JD requirements"""
    must_have_skills: List[str]  # Top 10 critical skills
    years_of_experience: dict  # {"min": 3, "max": 5, "total": 4}
    domain_keywords: List[str]  # Industry/domain terms
    role_seniority: str  # "Junior", "Mid", "Senior", "Lead", "Executive"
    nice_to_have_skills: List[str]  # Additional skills
    education: Optional[str]  # Degree requirements
    certifications: List[str]  # Required certifications


def parse_job_description(jd_text: str) -> JDRequirements:
    """
    Extract structured requirements from job description text.

    Args:
        jd_text: Raw job description text

    Returns:
        JDRequirements dict with all extracted fields
    """

    prompt = PromptTemplate(
        input_variables=["jd"],
        template="""
You are an expert recruiter analyzing job descriptions.

Job Description:
{jd}

TASK:
Extract structured hiring requirements. Be precise and thorough.

RULES:
1. must_have_skills: Extract EXACTLY the top 10 most critical technical/professional skills mentioned as required or must-have. If fewer than 10, list all required skills.
2. years_of_experience: Extract min/max years if mentioned, otherwise estimate based on role level
3. domain_keywords: Extract 5-8 industry/domain terms (e.g., "fintech", "healthcare", "cloud infrastructure")
4. role_seniority: Classify as one of: "Entry", "Junior", "Mid", "Senior", "Lead", "Principal", "Executive"
5. nice_to_have_skills: Extract 5-10 preferred/nice-to-have skills
6. education: Extract degree requirements (e.g., "Bachelor's in CS", "Master's preferred")
7. certifications: Extract any certifications mentioned (e.g., "AWS Certified", "PMP")

Return ONLY valid JSON (no markdown, no explanation):

{{
  "must_have_skills": ["Python", "AWS", "Docker", "Kubernetes", "CI/CD", "REST APIs", "SQL", "Linux", "Git", "Agile"],
  "years_of_experience": {{
    "min": 3,
    "max": 5,
    "total": 4
  }},
  "domain_keywords": ["cloud infrastructure", "DevOps", "microservices", "SaaS"],
  "role_seniority": "Mid",
  "nice_to_have_skills": ["Terraform", "Ansible", "Jenkins", "GraphQL", "React"],
  "education": "Bachelor's in Computer Science or related field",
  "certifications": ["AWS Certified Solutions Architect", "Kubernetes Administrator"]
}}
"""
    )

    llm = get_llm(temperature=0)
    response = llm.invoke(prompt.format(jd=jd_text))

    try:
        content = extract_json(response.content)

        parsed = json.loads(content)

        # Ensure must_have_skills is capped at 10
        if len(parsed.get("must_have_skills", [])) > 10:
            parsed["must_have_skills"] = parsed["must_have_skills"][:10]

        return parsed
    except json.JSONDecodeError:
        # Fallback to minimal structure if parsing fails
        return {
            "must_have_skills": [],
            "years_of_experience": {"min": 0, "max": 0, "total": 0},
            "domain_keywords": [],
            "role_seniority": "Unknown",
            "nice_to_have_skills": [],
            "education": None,
            "certifications": []
        }


def extract_top_skills(jd_text: str, limit: int = 10) -> List[str]:
    """
    Quick extraction of top N required skills from JD.

    Args:
        jd_text: Raw JD text
        limit: Maximum number of skills to extract (default 10)

    Returns:
        List of top required skills
    """
    parsed = parse_job_description(jd_text)
    return parsed["must_have_skills"][:limit]

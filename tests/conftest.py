"""
Shared pytest fixtures and Streamlit session state mock.

Usage:
    - Unit tests (scoring, risk, parser): no LLM needed, run directly
    - Integration tests: set env vars LLM_PROVIDER, LLM_API_KEY, LLM_MODEL
"""

import sys
import os
import types
from pathlib import Path
import pytest

# ---------------------------------------------------------------------------
# Project root setup (so 'from services.xxx import ...' works)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Streamlit mock — MUST be injected before any service imports
# ---------------------------------------------------------------------------
_mock_st = types.ModuleType("streamlit")


class _SessionState(dict):
    """Dict-like object that mimics st.session_state"""
    def get(self, key, default=None):
        return super().get(key, default)


_mock_st.session_state = _SessionState()

# Inject mock if streamlit not already imported
if "streamlit" not in sys.modules:
    sys.modules["streamlit"] = _mock_st


def configure_llm_from_env():
    """
    Configure the Streamlit session state mock with LLM credentials from env vars.
    Call this in integration tests that need LLM access.
    """
    provider = os.environ.get("LLM_PROVIDER")
    api_key = os.environ.get("LLM_API_KEY")
    model = os.environ.get("LLM_MODEL")

    if provider and api_key:
        st = sys.modules.get("streamlit", _mock_st)
        st.session_state["llm_configured"] = True
        st.session_state["llm_provider"] = provider
        st.session_state["llm_api_key"] = api_key
        if model:
            st.session_state["llm_model"] = model
        return True
    return False


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def project_root():
    """Project root path."""
    return PROJECT_ROOT


@pytest.fixture
def test_resumes_dir():
    """Path to test resume DOCX files."""
    return PROJECT_ROOT / "data" / "test_resumes"


@pytest.fixture
def test_jds_dir():
    """Path to test job description files."""
    return PROJECT_ROOT / "data" / "test_jds"


@pytest.fixture
def edge_cases_dir():
    """Path to edge case test files."""
    return PROJECT_ROOT / "data" / "test_resumes" / "edge_cases"


# ---------------------------------------------------------------------------
# Common mock data factories
# ---------------------------------------------------------------------------
@pytest.fixture
def make_resume_signals():
    """Factory for creating mock resume signals dicts."""
    def _make(
        skills=None,
        total_years=5,
        recent_years=2,
        positions=None,
        projects=None,
        measurable_outcomes=None,
        has_recent_experience=True,
        most_recent_role_year=2025,
        domain_experience=None,
        education="Bachelor's in Computer Science",
        certifications=None,
    ):
        return {
            "skills": skills or [],
            "experience_duration": {
                "total_years": total_years,
                "recent_years": recent_years,
                "positions": positions or [],
            },
            "projects": projects or [],
            "measurable_outcomes": measurable_outcomes or [],
            "recency_indicators": {
                "has_recent_experience": has_recent_experience,
                "most_recent_role_year": most_recent_role_year,
                "most_recent_role": "Engineer",
            },
            "domain_experience": domain_experience or [],
            "education": education,
            "certifications": certifications or [],
        }
    return _make


@pytest.fixture
def make_jd_requirements():
    """Factory for creating mock JD requirements dicts."""
    def _make(
        must_have_skills=None,
        min_years=5,
        max_years=10,
        domain_keywords=None,
        role_seniority="Senior",
        nice_to_have_skills=None,
        education=None,
        certifications=None,
    ):
        return {
            "must_have_skills": must_have_skills or [],
            "years_of_experience": {
                "min": min_years,
                "max": max_years,
                "total": (min_years + max_years) // 2,
            },
            "domain_keywords": domain_keywords or [],
            "role_seniority": role_seniority,
            "nice_to_have_skills": nice_to_have_skills or [],
            "education": education,
            "certifications": certifications or [],
        }
    return _make


@pytest.fixture
def devops_jd(make_jd_requirements):
    """Standard Senior DevOps JD for testing."""
    return make_jd_requirements(
        must_have_skills=[
            "aws", "docker", "kubernetes", "ci/cd", "terraform",
            "python", "linux", "git", "monitoring", "agile"
        ],
        min_years=5,
        max_years=10,
        domain_keywords=["saas", "cloud infrastructure", "microservices"],
        role_seniority="Senior",
    )

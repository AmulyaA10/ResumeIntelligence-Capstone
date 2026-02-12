"""
Parser edge case tests (resume_parser + jd_parser).

Run: python3 -m pytest tests/test_parsers_edge_cases.py -v
"""

import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from services.resume_parser import extract_text
from services import jd_parser


EDGE_DIR = Path(__file__).resolve().parent.parent / "data" / "test_resumes" / "edge_cases"


class DummyLLMResponse:
    def __init__(self, content: str):
        self.content = content


class DummyLLM:
    def __init__(self, content: str):
        self._content = content

    def invoke(self, _prompt: str):
        return DummyLLMResponse(self._content)


class TestResumeParserEdgeCases:
    def test_missing_file_raises(self):
        missing = EDGE_DIR / "does_not_exist.docx"
        with pytest.raises(FileNotFoundError):
            extract_text(str(missing))

    def test_unsupported_extension_raises(self, tmp_path):
        bad_file = tmp_path / "resume.txt"
        bad_file.write_text("plain text resume")
        with pytest.raises(ValueError):
            extract_text(str(bad_file))

    def test_empty_docx_returns_empty_string(self):
        text = extract_text(str(EDGE_DIR / "empty.docx"))
        assert text == ""

    def test_whitespace_docx_returns_empty_string(self):
        text = extract_text(str(EDGE_DIR / "whitespace_only.docx"))
        assert text == ""

    def test_table_only_docx_returns_empty_string(self):
        text = extract_text(str(EDGE_DIR / "table_only.docx"))
        assert text == ""


class TestJDParserEdgeCases:
    def test_invalid_json_falls_back(self, monkeypatch):
        def _fake_get_llm(*_args, **_kwargs):
            return DummyLLM("not json at all")

        monkeypatch.setattr(jd_parser, "get_llm", _fake_get_llm)

        result = jd_parser.parse_job_description("We need a senior engineer.")
        assert result["must_have_skills"] == []
        assert result["years_of_experience"] == {"min": 0, "max": 0, "total": 0}
        assert result["domain_keywords"] == []
        assert result["role_seniority"] == "Unknown"
        assert result["nice_to_have_skills"] == []
        assert result["education"] is None
        assert result["certifications"] == []

    def test_must_have_skills_capped_at_10(self, monkeypatch):
        skills = [f"skill_{i}" for i in range(12)]
        payload = {
            "must_have_skills": skills,
            "years_of_experience": {"min": 3, "max": 5, "total": 4},
            "domain_keywords": ["cloud", "devops"],
            "role_seniority": "Senior",
            "nice_to_have_skills": ["a", "b"],
            "education": "BS CS",
            "certifications": [],
        }
        content = str(payload).replace("'", "\"")

        def _fake_get_llm(*_args, **_kwargs):
            return DummyLLM(content)

        monkeypatch.setattr(jd_parser, "get_llm", _fake_get_llm)

        result = jd_parser.parse_job_description("JD")
        assert len(result["must_have_skills"]) == 10

    def test_extract_top_skills_respects_limit(self, monkeypatch):
        skills = [f"skill_{i}" for i in range(10)]
        payload = {
            "must_have_skills": skills,
            "years_of_experience": {"min": 3, "max": 5, "total": 4},
            "domain_keywords": ["cloud"],
            "role_seniority": "Mid",
            "nice_to_have_skills": [],
            "education": None,
            "certifications": [],
        }
        content = str(payload).replace("'", "\"")

        def _fake_get_llm(*_args, **_kwargs):
            return DummyLLM(content)

        monkeypatch.setattr(jd_parser, "get_llm", _fake_get_llm)

        top3 = jd_parser.extract_top_skills("JD", limit=3)
        assert top3 == skills[:3]

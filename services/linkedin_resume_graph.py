from typing import TypedDict, Optional, Dict
from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph, END
from services.llm_config import get_llm, extract_json
import json

class LinkedInResumeState(TypedDict):
    linkedin_url: str
    raw_profile: Optional[str]
    parsed_profile: Optional[Dict]
    resume: Optional[str]


def linkedin_fetch_agent(state: LinkedInResumeState):
    # MOCKED profile content (placeholder for real LinkedIn API integration)
    mock_profile = """
Name: Rahul Sharma
Headline: Senior AI Engineer
Experience:
- AI Engineer at ABC Corp (2021-Present)
- Data Scientist at XYZ Ltd (2019-2021)
Skills:
Python, LangChain, AWS, Docker, Machine Learning
Education:
B.Tech in Computer Science
"""
    return {"raw_profile": mock_profile}


def profile_parser_agent(state: LinkedInResumeState):
    prompt = PromptTemplate(
        input_variables=["profile"],
        template="""
Extract structured resume data from LinkedIn profile text.

Profile:
{profile}

Return ONLY valid JSON:
{{
  "name": "",
  "headline": "",
  "experience": [],
  "skills": [],
  "education": []
}}
"""
    )

    llm = get_llm(temperature=0.3)
    response = llm.invoke(
        prompt.format(profile=state["raw_profile"])
    )

    content = extract_json(response.content)
    try:
        return {"parsed_profile": json.loads(content)}
    except json.JSONDecodeError:
        return {"parsed_profile": {"name": "", "headline": "", "experience": [], "skills": [], "education": []}}

def resume_writer_agent(state: LinkedInResumeState):
    profile = state["parsed_profile"]

    prompt = PromptTemplate(
        input_variables=["profile"],
        template="""
You are a professional resume writer.

Create a clean, ATS-friendly resume using this data:

{profile}

Rules:
- Professional tone
- Bullet points
- One page
"""
    )

    llm = get_llm(temperature=0.3)
    response = llm.invoke(
        prompt.format(profile=json.dumps(profile, indent=2))
    )

    return {"resume": response.content}


def build_linkedin_resume_graph():
    graph = StateGraph(LinkedInResumeState)

    graph.add_node("fetch", linkedin_fetch_agent)
    graph.add_node("parse", profile_parser_agent)
    graph.add_node("write", resume_writer_agent)

    graph.set_entry_point("fetch")

    graph.add_edge("fetch", "parse")
    graph.add_edge("parse", "write")
    graph.add_edge("write", END)

    return graph.compile()

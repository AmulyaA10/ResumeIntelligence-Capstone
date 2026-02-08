from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

import os, json
from dotenv import load_dotenv
load_dotenv()
# -----------------------------
# State
# -----------------------------
class ResumeQualityState(TypedDict):
    resumes: List[str]
    parsed: Optional[str]
    score: Optional[dict]


# -----------------------------
# LLM
# -----------------------------
#llm = ChatOpenAI(
   # model="gpt-4o-mini",
   # temperature=0,
  #  api_key=os.getenv("OPENAI_API_KEY")
#)

llm = ChatOpenAI(
    model="openai/gpt-4o-mini",
    temperature=0,
    api_key=os.getenv("OPEN_ROUTER_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

print(os.getenv("OPENAI_API_KEY"))
# -----------------------------ssss
# Agents
# -----------------------------
def resume_reader_agent(state: ResumeQualityState):
    resume_text = state["resumes"][0]
    return {"parsed": resume_text}


def quality_scoring_agent(state: ResumeQualityState):
    prompt = PromptTemplate(
    input_variables=["resume"],
    template="""
You are an expert resume reviewer.

Resume:
{resume}

TASK:
Evaluate resume quality on a scale of 0–100.

Return ONLY valid JSON:

{{
  "clarity": 0,
  "skills": 0,
  "format": 0,
  "overall": 0
}}
"""
)

    response = llm.invoke(
        prompt.format(resume=state["parsed"])
    )

    return {"score": json.loads(response.content)}


# -----------------------------
# Graph
# -----------------------------
def build_resume_quality_graph():
    graph = StateGraph(ResumeQualityState)

    graph.add_node("reader", resume_reader_agent)
    graph.add_node("score", quality_scoring_agent)

    graph.set_entry_point("reader")
    graph.add_edge("reader", "score")
    graph.add_edge("score", END)

    return graph.compile()

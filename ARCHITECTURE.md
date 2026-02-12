# Architecture - Resume Intelligence Platform

## Overview

This is a **multi-page Streamlit application** that uses **LangGraph agentic workflows** and **LangChain** to provide AI-powered resume screening, scoring, and candidate ranking. Users select their preferred LLM provider via the sidebar UI — no hardcoded API keys.

---

## Tech Stack

| Layer            | Technology                                      |
|------------------|--------------------------------------------------|
| Frontend         | Streamlit (multi-page app)                       |
| AI Orchestration | LangGraph (StateGraph with typed state machines) |
| LLM Abstraction  | LangChain (ChatOpenAI, ChatAnthropic, ChatGroq, ChatGoogleGenerativeAI) |
| Vector Database  | LanceDB (local, file-based)                      |
| File Parsing     | PyPDF, python-docx                               |
| Data Processing  | Pandas, PyArrow                                  |

---

## Project Structure

```
ResumeIntelligence/
├── Home.py                          # Entry point + sidebar LLM config
├── Pages/                           # Streamlit multi-page directory
│   ├── 1_Upload_Resumes.py          # PDF/DOCX upload + LanceDB storage
│   ├── 2_Search_Resumes.py          # LLM-powered semantic search
│   ├── 3_Resume_Quality_Scoring.py  # LangGraph quality scoring agent
│   ├── 4_Skill_Gap_Analysis.py      # LangGraph skill gap agents
│   ├── 5_Auto_Screening.py          # Threshold-based auto screening
│   ├── 6_Resume_Generator.py        # AI resume writer
│   ├── 7_LinkedIn_To_Resume.py      # LinkedIn profile to resume
│   ├── 8_Reports_Export.py          # CSV export for results
│   └── 9_JD_Resume_Matching.py      # Full matching pipeline (primary feature)
├── services/                        # Core business logic
│   ├── llm_config.py                # Multi-provider LLM factory
│   ├── matching_workflow.py         # LangGraph JD-Resume matching pipeline
│   ├── jd_parser.py                 # LLM: extracts structured JD requirements
│   ├── resume_enricher.py           # LLM: extracts structured resume signals
│   ├── risk_detector.py             # Rule-based: detects risk flags
│   ├── scoring_engine.py            # Rule-based: 100-point scoring rubric
│   ├── explainer.py                 # Rule-based: generates explanations
│   ├── resume_quality_graph.py      # LangGraph: resume quality workflow
│   ├── skill_gap_graph.py           # LangGraph: skill gap workflow
│   ├── linkedin_resume_graph.py     # LangGraph: LinkedIn to resume workflow
│   ├── agent_controller.py          # Facade for Pages 3-5 (routes tasks)
│   ├── resume_parser.py             # PDF/DOCX text extraction
│   └── db/
│       └── lancedb_client.py        # LanceDB storage client
├── data/                            # Runtime data (resumes, DB files)
├── requirements.txt
└── test_matching.py                 # Integration test
```

---

## How the Main Pipeline Works (Page 9: JD-Resume Matching)

This is the primary feature. It runs a **3-node LangGraph StateGraph**:

```
┌─────────────┐     ┌──────────────────┐     ┌──────────┐
│  JD Parser   │────>│ Resume Processor  │────>│  Ranker   │──── END
│  (Agent 1)   │     │   (Agent 2)       │     │ (Agent 3) │
└─────────────┘     └──────────────────┘     └──────────┘
```

### Agent 1: JD Parser
- **Input:** Raw job description text
- **Uses:** `jd_parser.py` (LLM call)
- **Output:** Structured requirements (must-have skills, experience years, seniority, domain keywords)

### Agent 2: Resume Batch Processor
For each resume, runs this sub-pipeline:

```
Resume Text
    │
    ├── resume_enricher.py  (LLM)  → Structured signals (skills + context, experience, education)
    │
    ├── risk_detector.py    (Rules) → Risk flags (skills without context, gaps, job hopping, etc.)
    │
    ├── scoring_engine.py   (Rules) → 100-point score breakdown
    │                                   ├── Skill Coverage      (30 pts)
    │                                   ├── Experience Depth     (20 pts)
    │                                   ├── Domain Relevance     (15 pts)
    │                                   ├── Evidence Quality     (15 pts)
    │                                   ├── Quantification       (10 pts)
    │                                   ├── Recency              (10 pts)
    │                                   └── Risk Penalties       (up to -20 pts)
    │
    └── explainer.py        (Rules) → Human-readable explanation + recommendation
```

### Agent 3: Ranker
- Sorts all candidates by final score (descending)
- Assigns rank numbers

### Output
Each candidate gets:
- **Score:** 0-100 with 6-component breakdown
- **Recommendation:** Shortlist / Review / Reject
- **Explanation:** Detailed reasoning for the score
- **Summary:** One-line summary

---

## 100-Point Scoring Rubric

| Component          | Max Points | What It Measures                                    |
|--------------------|------------|-----------------------------------------------------|
| Skill Coverage     | 30         | % of required JD skills found in resume             |
| Experience Depth   | 20         | Years of experience vs. JD requirement              |
| Domain Relevance   | 15         | Overlap between resume domain and JD domain         |
| Evidence Quality   | 15         | Skills backed by project context (not just listed)  |
| Quantification     | 10         | Measurable outcomes (numbers, percentages, metrics) |
| Recency            | 10         | How recent the relevant experience is               |
| **Risk Penalties** | **-20**    | Job hopping, gaps, skills without context            |

---

## LLM Configuration

The platform supports **6 providers** with **25+ models**, configured at runtime via the sidebar:

| Provider              | Models                                    | API Key Source         |
|-----------------------|-------------------------------------------|------------------------|
| OpenAI                | gpt-4o-mini, gpt-4o, gpt-4-turbo, gpt-3.5-turbo | platform.openai.com |
| Anthropic (Claude)    | claude-sonnet-4, claude-3.5-haiku, claude-3-opus | console.anthropic.com |
| Google Gemini         | gemini-2.0-flash, gemini-1.5-flash, gemini-1.5-pro | aistudio.google.com |
| Groq                  | llama-3.3-70b, llama-3.1-8b, mixtral-8x7b, gemma2-9b | console.groq.com |
| OpenRouter            | Multiple paid models via unified API      | openrouter.ai          |
| Free Models (OpenRouter) | Free-tier models (no cost)             | openrouter.ai          |

**How it works:**
1. User selects provider + pastes API key in sidebar
2. Config stored in `st.session_state`
3. Every service calls `get_llm()` which reads session state and instantiates the correct LangChain class
4. `extract_json()` helper strips markdown code fences (non-OpenAI models often wrap JSON in backticks)

---

## LangGraph Workflows

The app uses **4 LangGraph StateGraph workflows**:

| Workflow               | File                        | Nodes | Used By        |
|------------------------|-----------------------------|-------|----------------|
| JD-Resume Matching     | `matching_workflow.py`      | 3     | Page 9         |
| Resume Quality Scoring | `resume_quality_graph.py`   | 2     | Pages 3, 5     |
| Skill Gap Analysis     | `skill_gap_graph.py`        | 2     | Page 4         |
| LinkedIn to Resume     | `linkedin_resume_graph.py`  | 2     | Page 7         |

Each workflow uses **TypedDict state classes** for type-safe state management across nodes.

---

## Data Flow

```
User uploads PDF/DOCX
        │
        ▼
resume_parser.py (extract text)
        │
        ▼
LanceDB (store text + filename)
        │
        ▼
User provides JD + selects resumes
        │
        ▼
matching_workflow.py (LangGraph)
   ├── jd_parser.py       → structured requirements
   ├── resume_enricher.py  → structured signals
   ├── risk_detector.py    → risk flags
   ├── scoring_engine.py   → 100-point scores
   ├── explainer.py        → explanations
   └── ranker              → sorted results
        │
        ▼
Streamlit UI (colored table, charts, expandable reports)
        │
        ▼
CSV Export (ranking table + shortlist)
```

---

## What Uses LLM vs. Rules

| Component        | LLM or Rules | Why                                              |
|------------------|--------------|--------------------------------------------------|
| JD Parser        | LLM          | Natural language understanding of JD requirements |
| Resume Enricher  | LLM          | Extract structured signals from unstructured text |
| Risk Detector    | Rules        | Deterministic, explainable risk flags             |
| Scoring Engine   | Rules        | Reproducible, auditable 100-point scoring         |
| Explainer        | Rules        | Consistent explanation format                     |
| Resume Generator | LLM          | Creative writing for ATS-optimized resumes        |
| Resume Search    | LLM          | Semantic matching across resume corpus            |

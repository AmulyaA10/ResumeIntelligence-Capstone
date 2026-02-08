# Resume Intelligence MVP - System Architecture

## 📐 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        STREAMLIT FRONTEND                            │
│  Pages/9_🎯_JD_Resume_Matching.py - Main Dashboard                  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    LANGGRAPH WORKFLOW LAYER                          │
│  services/matching_workflow.py - Orchestration                      │
│                                                                       │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐            │
│  │ JD Parser   │ -> │  Resume     │ -> │  Ranking    │            │
│  │   Agent     │    │ Processor   │    │   Agent     │            │
│  └─────────────┘    └─────────────┘    └─────────────┘            │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       CORE SERVICE LAYER                             │
│                                                                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │
│  │  jd_parser.py    │  │resume_enricher.py│  │risk_detector.py  │ │
│  │  - Extract       │  │  - Extract       │  │  - Detect flags  │ │
│  │    skills        │  │    signals       │  │  - Calculate     │ │
│  │  - Extract       │  │  - Projects      │  │    penalties     │ │
│  │    requirements  │  │  - Metrics       │  │                  │ │
│  │  - Domain        │  │  - Recency       │  │                  │ │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘ │
│                                                                       │
│  ┌──────────────────┐  ┌──────────────────┐                        │
│  │scoring_engine.py │  │  explainer.py    │                        │
│  │  - 6 components  │  │  - Generate      │                        │
│  │  - 100-pt rubric │  │    explanations  │                        │
│  │  - Final score   │  │  - Recommend     │                        │
│  └──────────────────┘  └──────────────────┘                        │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          LLM LAYER                                   │
│  - OpenRouter / OpenAI GPT-4o-mini                                  │
│  - Used for: JD parsing, Resume signal extraction                   │
│  - NOT used for: Scoring (rule-based)                               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow: JD-Resume Matching

```
1. USER INPUT
   ├─ Job Description (text or file)
   └─ Resumes (files, DB, or text)
          ↓
2. LANGGRAPH WORKFLOW STARTS
          ↓
3. JD PARSER AGENT
   ├─ Input: JD text
   ├─ Process: LLM extracts structured requirements
   └─ Output: {must_have_skills, years_of_experience, domain_keywords, role_seniority, ...}
          ↓
4. RESUME BATCH PROCESSOR AGENT (for each resume)
   ├─ Step 4.1: Resume Enricher
   │   ├─ Input: Resume text
   │   ├─ Process: LLM extracts signals
   │   └─ Output: {skills, experience_duration, projects, measurable_outcomes, ...}
   │
   ├─ Step 4.2: Risk Detector
   │   ├─ Input: Resume signals + JD requirements
   │   ├─ Process: Rule-based flag detection
   │   └─ Output: {flags: [...], total_penalty: 0-20}
   │
   ├─ Step 4.3: Scoring Engine
   │   ├─ Input: Resume signals + JD requirements + Risk flags
   │   ├─ Process: Calculate 6 component scores
   │   └─ Output: {final_score: 0-100, breakdown: {...}, penalty: ...}
   │
   └─ Step 4.4: Explainer
       ├─ Input: Score result
       ├─ Process: Generate markdown explanation
       └─ Output: {explanation: "...", recommendation: "Shortlist/Review/Reject"}
          ↓
5. RANKING AGENT
   ├─ Input: List of candidates with scores
   ├─ Process: Sort by final_score (descending)
   └─ Output: ranked_candidates (with rank numbers)
          ↓
6. STREAMLIT DISPLAY
   ├─ Ranking table (colored by recommendation)
   ├─ Expandable candidate details
   ├─ Score breakdown charts
   └─ Export options (CSV)
```

---

## 📊 Scoring Engine Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      SCORING ENGINE                                  │
│                  (services/scoring_engine.py)                        │
└─────────────────────────────────────────────────────────────────────┘

Input: resume_signals, jd_requirements, risk_flags

┌──────────────────────────┐
│  COMPONENT CALCULATORS   │  (Each returns score + details)
└──────────────────────────┘

1. calculate_skill_coverage_score()
   ├─ Match resume skills to JD must-have skills
   ├─ 3 pts per match (max 10 skills = 30 pts)
   ├─ +0.5 bonus for strong context
   └─ Returns: {score: 0-30, matched_skills, missing_skills, ...}

2. calculate_experience_depth_score()
   ├─ Compare resume years to JD min years
   ├─ 10 pts for meeting min, +2 pts per extra year
   ├─ +2 pts for seniority match
   └─ Returns: {score: 0-20, resume_years, required_years, ...}

3. calculate_domain_relevance_score()
   ├─ Match resume domains to JD domains
   ├─ 5 pts per domain match (max 3 = 15 pts)
   └─ Returns: {score: 0-15, matched_domains, required_domains, ...}

4. calculate_evidence_quality_score()
   ├─ Check projects mentioned (5-8 pts)
   ├─ Check skills with context (7 pts if 80%+)
   └─ Returns: {score: 0-15, projects_count, skills_with_context, ...}

5. calculate_quantification_score()
   ├─ Count measurable outcomes
   ├─ 0 outcomes: 0 pts, 1-2: 5 pts, 3-4: 8 pts, 5+: 10 pts
   └─ Returns: {score: 0-10, outcomes_count, sample_outcomes, ...}

6. calculate_recency_score()
   ├─ Check most recent role year
   ├─ 2023+: 10 pts, 2022+: 7 pts, 2020-2021: 4 pts, <2020: 0 pts
   └─ Returns: {score: 0-10, most_recent_year, ...}

                      ↓
┌──────────────────────────┐
│  TOTAL SCORE CALCULATOR  │
└──────────────────────────┘

base_score = sum of all 6 component scores (0-100)
penalty = risk_flags.total_penalty (0-20)
final_score = max(0, min(100, base_score - penalty))

                      ↓
Output: {
  final_score: 85,
  base_score: 93,
  penalty: 8,
  breakdown: {
    skill_coverage: {...},
    experience_depth: {...},
    domain_relevance: {...},
    evidence_quality: {...},
    quantification: {...},
    recency: {...}
  },
  risk_flags: {...}
}
```

---

## 🚩 Risk Detection Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     RISK DETECTOR                                    │
│                  (services/risk_detector.py)                         │
└─────────────────────────────────────────────────────────────────────┘

Input: resume_signals, jd_requirements

┌──────────────────────────┐
│   FLAG DETECTION RULES   │
└──────────────────────────┘

1. WEAK_EVIDENCE (-5 pts)
   └─ If 3+ skills have NO context or context < 20 chars

2. NO_QUANTIFICATION (-5 pts)
   └─ If measurable_outcomes list is empty

3. LOW_QUANTIFICATION (-3 pts)
   └─ If only 1 measurable outcome

4. BUZZWORD_HEAVY (-4 pts)
   └─ If 5+ buzzwords found (synergy, leverage, disrupt, ...)

5. BUZZWORD_MODERATE (-2 pts)
   └─ If 3-4 buzzwords found

6. OUTDATED_EXPERIENCE (-4 pts)
   └─ If most_recent_role_year < 2022

7. NO_PROJECTS (-3 pts)
   └─ If projects list is empty

8. DOMAIN_MISMATCH (-3 pts)
   └─ If JD domains != resume domains

9. EXPERIENCE_GAP (-2 pts)
   └─ If resume years < JD min years

                      ↓
Output: RiskFlags {
  flags: [
    {category: "WEAK_EVIDENCE", description: "...", penalty: 5},
    {category: "BUZZWORD_MODERATE", description: "...", penalty: 2}
  ],
  total_penalty: 7  (capped at 20)
}
```

---

## 🧩 Module Dependencies

```
Pages/9_🎯_JD_Resume_Matching.py
    └─ matching_workflow.py
           ├─ jd_parser.py
           │     └─ langchain_openai (LLM)
           │
           ├─ resume_enricher.py
           │     └─ langchain_openai (LLM)
           │
           ├─ risk_detector.py
           │     └─ (no LLM, pure rules)
           │
           ├─ scoring_engine.py
           │     └─ (no LLM, pure rules)
           │
           └─ explainer.py
                 └─ (no LLM, pure text generation)
```

**Key Design Principle**: Only use LLM for **extraction** (NLP tasks), never for **scoring** (use deterministic rules for explainability).

---

## 📁 File Organization

```
ResumeIntelligence/
├── app.py                          # Streamlit entry point
├── Pages/
│   ├── 1_📂_Upload_Resumes.py      # [Existing]
│   ├── 2_🔍_Search_Resumes.py      # [Existing]
│   ├── 3_📊_Resume_Quality_Scoring.py  # [Existing]
│   ├── 4_🧠_Skill_Gap_Analysis.py  # [Existing]
│   ├── 5_🤖_Auto_Screening.py      # [Existing]
│   ├── 6_📝_Resume_Generator.py    # [Existing]
│   ├── 7_🔗_LinkedIn_To_Resume.py  # [Existing]
│   ├── 8_📥_Reports_Export.py      # [Existing]
│   └── 9_🎯_JD_Resume_Matching.py  # [NEW] Main PRD feature
│
├── services/
│   ├── resume_parser.py            # [Existing] Basic text extraction
│   ├── jd_parser.py                # [NEW] JD requirement extraction
│   ├── resume_enricher.py          # [NEW] Enhanced resume parsing
│   ├── risk_detector.py            # [NEW] Risk flag detection
│   ├── scoring_engine.py           # [NEW] 100-point rubric
│   ├── explainer.py                # [NEW] Explanation generation
│   ├── matching_workflow.py        # [NEW] LangGraph orchestration
│   ├── agent_controller.py         # [Existing] Old workflows
│   ├── resume_quality_graph.py     # [Existing]
│   ├── skill_gap_graph.py          # [Existing]
│   ├── linkedin_resume_graph.py    # [Existing]
│   └── db/
│       └── lancedb_client.py       # [Existing] Vector DB
│
├── test_matching.py                # [NEW] Test script
├── IMPLEMENTATION_SUMMARY.md       # [NEW] Documentation
├── ARCHITECTURE.md                 # [NEW] This file
└── requirements.txt                # [Existing] Dependencies
```

---

## 🔧 Technology Stack

### Frontend
- **Streamlit**: Multi-page dashboard UI
- **Pandas**: Data tables and manipulation
- **Markdown**: Report formatting

### Backend
- **LangGraph**: Agent workflow orchestration
- **LangChain**: LLM abstraction layer
- **OpenRouter / OpenAI**: LLM API (GPT-4o-mini)
- **Python 3.11**: Core language

### Storage
- **LanceDB**: Vector database for resume storage
- **CSV**: Export format

### Parsing
- **PyPDF**: PDF text extraction
- **python-docx**: DOCX text extraction

---

## ⚡ Performance Characteristics

### Latency
- **JD Parsing**: ~2-3 seconds (1 LLM call)
- **Resume Processing**: ~5-10 seconds per resume (2 LLM calls)
- **Batch Processing**: ~5-10 seconds × N resumes (parallel possible in future)

### API Costs (Estimated)
- **GPT-4o-mini**: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens
- **Per Resume**: ~3-4 LLM calls = ~$0.001-0.002 per resume
- **100 Resumes**: ~$0.10-0.20 total

### Scalability
- **Current**: Sequential processing (1 resume at a time)
- **Future**: Parallel processing (10-50 resumes simultaneously)
- **Database**: LanceDB handles millions of resumes

---

## 🎯 Key Differentiators (vs Simple Keyword Matching)

| Feature | Keyword Matching | Our System |
|---------|------------------|------------|
| **Skill Detection** | Exact match only | Context-aware (checks WHERE skill was used) |
| **Evidence Quality** | Not evaluated | Checks projects, quantified outcomes |
| **Recency** | Ignored | Penalizes outdated experience |
| **Buzzwords** | Often boosted | Penalized (red flag) |
| **Explainability** | None | Full markdown breakdown per component |
| **False Positives** | High (buzzword-heavy resumes pass) | Low (risk flags catch vague claims) |
| **Scoring** | Binary (match/no match) | Nuanced (0-100 with 6 components) |

---

## 🧪 Testing Strategy

### Unit Tests (Recommended)
- `test_jd_parser.py`: Validate JD extraction accuracy
- `test_resume_enricher.py`: Validate signal extraction
- `test_scoring_engine.py`: Validate score calculations
- `test_risk_detector.py`: Validate flag detection logic

### Integration Test
- `test_matching.py`: End-to-end workflow (already created)

### User Acceptance Testing
- Test with 20-50 real resumes
- Compare rankings to human recruiter judgments
- Measure agreement rate (target: >80%)

---

## 📈 Future Enhancements

### Semantic Matching
- Use embeddings for skill similarity (e.g., "React" ≈ "React.js")
- Domain-specific skill graphs

### Confidence Scores
- Add confidence levels to extracted data (High/Medium/Low)
- Adjust scoring based on extraction confidence

### Calibration
- Track hire outcomes (hired/rejected after interview)
- Adjust rubric weights based on historical success

### Multi-Modal
- Parse resume images (screenshots, scanned PDFs)
- Extract data from LinkedIn profile URLs (no scraping, use API)

---

## ✅ Production Checklist

- [x] All FR1-FR5 requirements implemented
- [x] 100-point rubric with explainability
- [x] Risk flag detection
- [x] Streamlit dashboard UI
- [x] Export functionality
- [ ] Valid API keys configured in `.env`
- [ ] Test with 20+ real resumes
- [ ] Validate scoring accuracy vs human baseline
- [ ] Optimize LLM prompts for cost/quality
- [ ] Add error handling for malformed resumes
- [ ] Add logging for debugging
- [ ] Deploy to cloud (AWS/GCP/Azure) or local server

---

**Architecture Version**: 1.0
**Last Updated**: February 8, 2026
**Status**: ✅ Implementation Complete

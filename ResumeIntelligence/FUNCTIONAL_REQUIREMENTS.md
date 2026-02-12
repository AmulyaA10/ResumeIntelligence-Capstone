# Functional Requirements — Resume Intelligence Platform

> Each FR is one detailed line describing exactly what the system does, with specific scoring rubrics, point values, thresholds, and data structures.

---

## 1. Resume Ingestion & Storage

**FR-1:** Users can bulk-upload multiple PDF/DOCX resume files, which are parsed into plain text via `pypdf`/`python-docx` and persisted both as raw files in `data/raw_resumes/` and as structured records (UUID `id`, `filename`, `text`, `fingerprint`, `signals`) in a LanceDB vector table using a PyArrow schema.

**FR-2:** Each uploaded resume is stored in LanceDB with an auto-generated UUID-4 identifier, SHA-256 content fingerprint for deduplication, and optionally pre-extracted structured signals (JSON) — the system creates the `data/lancedb/` directory and `resumes` table on first use if they don't exist, with automatic schema migration for older tables.

**FR-3:** Corrupt or unreadable files are caught per-file with try/except so that one bad upload does not abort the entire batch — the user sees individual error messages and a final count of successfully processed files.

**FR-3a:** At upload time, if an LLM provider is configured, the system pre-extracts structured resume signals (skills, experience, projects, measurable outcomes, recency, domain, education, certifications) and caches them in LanceDB alongside the raw text — enabling faster JD-resume matching on subsequent runs by skipping redundant LLM calls; uploads still work fully without an LLM configured (signals are extracted lazily on first match).

---

## 2. LLM-Powered Resume Search

**FR-4:** Users enter a natural-language query (e.g., "DevOps Engineer with AWS and CI/CD") and the system sends up to 50 stored resumes (each truncated to 3,000 chars) to the configured LLM, which returns a ranked JSON array of matches with `filename`, `score` (0–100), `justification` (2–4 sentences), `missing_skills` array, and `auto_screen` ("Selected"/"Rejected"), displayed with metrics, skill gap lists, and resume download buttons.

---

## 3. Resume Quality Scoring

**FR-5:** A LangGraph 2-node workflow (`reader` → `score`) sends the pasted resume to the LLM, which returns four independent 0–100 scores — `clarity`, `skills`, `format`, and `overall` — displayed as a JSON breakdown with a headline metric.

---

## 4. Skill Gap Analysis

**FR-6:** A LangGraph 3-node workflow (`resume_skills` → `jd_skills` → `compare`) uses the LLM to independently extract skill lists from both the resume and job description, then computes the set difference to produce `missing_skills` (all gaps) and `recommended` (top 5 skills to learn), displayed in side-by-side red/green columns.

---

## 5. Auto Screening

**FR-7:** The system runs the resume quality scoring workflow and applies a user-configurable threshold slider (range 50–90, default 75) to produce a binary `Selected`/`Rejected` decision with a reason string, displayed alongside the score metric in a two-column layout.

---

## 6. Resume Generation

**FR-8:** Users describe their background in free text with an optional target role, and the LLM (temperature 0.3) generates a clean, ATS-optimized, one-page-equivalent resume using the structure Name → Summary → Experience → Skills → Education with action-verb bullet points and quantified achievements, available for download as `.txt`.

---

## 7. LinkedIn to Resume

**FR-9:** A LangGraph 3-node pipeline (`fetch` → `parse` → `write`) takes a LinkedIn URL, extracts structured profile data (name, headline, experience, skills, education) via the LLM, and generates a professional resume — currently using a hardcoded mock profile as a placeholder for real LinkedIn API integration.

---

## 8. Reports & Export

**FR-10:** Users can export the full LanceDB resume database as a CSV (with text truncated to 500-char previews), and separately export JD-resume matching results — including Rank, Candidate ID, Final Score, Recommendation, Skills Matched/Missing, Experience Years, Penalty, and Summary — with an additional shortlist-only CSV download option.

---

## 9. JD-Resume Matching & Ranking *(Primary Feature)*

**FR-11:** The LLM (temperature 0) parses a raw job description into 7 structured fields: `must_have_skills` (top 10, capped), `years_of_experience` (min/max/total), `domain_keywords` (5–8 terms), `role_seniority` (one of Entry/Junior/Mid/Senior/Lead/Principal/Executive), `nice_to_have_skills` (5–10), `education`, and `certifications` — with a safe fallback to empty/zero defaults on JSON parse failure.

**FR-12:** The LLM (temperature 0) extracts 8 structured signal fields from each resume: `skills` (with usage context per skill), `experience_duration` (total years, recent years, position list), `projects` (name/description/impact), `measurable_outcomes` (only quantified achievements with %, $, numbers), `recency_indicators` (has_recent_experience flag + most_recent_role_year using dynamic `CURRENT_YEAR`), `domain_experience`, `education`, and `certifications` — with safe fallback defaults.

**FR-13:** A rule-based 100-point scoring engine evaluates each candidate across 6 weighted dimensions: Skill Coverage (0–30 pts: 3 pts per matched must-have skill + 0.5 bonus for skills with >30-char context), Experience Depth (0–20 pts: 10 pts for meeting minimum years + 2 pts per extra year up to 5 + 2 pts seniority match), Domain Relevance (0–15 pts: 5 pts per matching domain keyword, max 3), Evidence Quality (0–15 pts: 5–8 pts for projects + 2–7 pts for skills-with-context ratio), Quantification (0–10 pts: 0/5/8/10 pts for 0/1–2/3–4/5+ measurable outcomes), and Recency (0–10 pts: 10/7/4/0 pts based on most recent role year relative to `CURRENT_YEAR`).

**FR-14:** A rule-based risk detector scans each candidate for 9 risk categories — WEAK_EVIDENCE (−5 pts for 3+ skills without action-verb context), NO_QUANTIFICATION (−5 pts), LOW_QUANTIFICATION (−3 pts), BUZZWORD_HEAVY (−4 pts for 5+ buzzwords from a 20-word watchlist), BUZZWORD_MODERATE (−2 pts for 3–4 buzzwords), OUTDATED_EXPERIENCE (−4 pts if most recent role is >2 years old), NO_PROJECTS (−3 pts), DOMAIN_MISMATCH (−3 pts), and EXPERIENCE_GAP (−2 pts) — with total penalty capped at −20 points.

**FR-15:** The final score (`base_score − penalty`, clamped 0–100) drives a 3-tier recommendation: **Shortlist** (≥75), **Review** (60–74), or **Reject** (<60).

**FR-16:** For each candidate, the system generates a full Markdown evaluation report containing: final score header, recommendation badge, base score vs penalty summary, 6 detailed component explanations (with matched/missing skill lists, year comparisons, domain matches, project counts, outcome samples, recency assessment), risk flag details with per-flag category/description/penalty, and a next-steps summary.

**FR-17:** A LangGraph 3-node StateGraph workflow (`jd_parser` → `resume_batch_processor` → `ranker`) orchestrates the entire pipeline — parsing the JD once, then for each resume: extracting signals, detecting risks, scoring, generating explanation/recommendation/summary — and finally sorting all candidates by score descending with assigned rank numbers.

**FR-18:** Results are displayed as a color-coded ranking table (green = Shortlist, yellow = Review, red = Reject) with columns for Rank, Score, Recommendation, Skills Match ratio, Experience years, and Penalties, plus expandable per-candidate detail cards showing the full Markdown report and a 6-component bar chart, with CSV export for the full table and shortlist-only subset.

---

## 10. Multi-LLM Provider Support

**FR-19:** The sidebar UI lets users choose from 6 providers (OpenAI, Anthropic Claude, Google Gemini, Groq, OpenRouter, Free Models via OpenRouter) spanning 25+ models, enter their API key, and select a specific model — all persisted in Streamlit `session_state` (`llm_provider`, `llm_api_key`, `llm_model`, `llm_configured`) and available across all pages without restart.

**FR-20:** The `get_llm()` factory uses lazy imports to instantiate provider-specific LangChain chat models (`ChatOpenAI`, `ChatAnthropic`, `ChatGoogleGenerativeAI`, `ChatGroq`) only when called, and the `extract_json()` helper strips markdown code fences (` ```json ... ``` `) from non-OpenAI model responses to ensure reliable JSON parsing.

---

## 11. Error Handling & Production Guards

**FR-21:** All 7 AI-powered pages (2–7, 9) check `st.session_state.get("llm_configured")` before any LLM call and show a clear sidebar-configuration prompt if missing, all LLM calls are wrapped in try/except blocks surfacing user-friendly `st.error()` messages, and all 4 LangGraph workflows include JSON parse fallbacks returning safe default structures on `JSONDecodeError` to prevent unhandled crashes.

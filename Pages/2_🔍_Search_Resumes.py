import os
import json
from pathlib import Path
import streamlit as st
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from services.db.lancedb_client import get_or_create_table
from services.llm_config import get_llm, extract_json

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESUME_DIR = str(PROJECT_ROOT / "data" / "raw_resumes")

st.title("🔍 Resume Search")
st.caption("LLM-powered semantic search across all stored resumes.")

# -----------------------------
# Load resumes from LanceDB
# -----------------------------
table = get_or_create_table()
df = table.to_pandas()

if df.empty:
    st.warning("No resumes found. Please upload resumes first.")
    st.stop()

MAX_RESUMES = 50
if len(df) > MAX_RESUMES:
    st.warning(f"Database contains {len(df)} resumes. Searching the most recent {MAX_RESUMES}.")
    df = df.tail(MAX_RESUMES)

st.info(f"Searching across {len(df)} resumes")

# -----------------------------
# User input
# -----------------------------
query = st.text_input(
    "Search resumes (skills, role, name, experience)",
    placeholder="e.g. DevOps Engineer with AWS and CI/CD"
)

if not query:
    st.stop()

# -----------------------------
# Prepare resume text for LLM
# -----------------------------
resumes_text = ""
for _, row in df.iterrows():
    # Truncate individual resumes to avoid exceeding context limits
    text = row['text'][:3000]
    resumes_text += f"""
Filename: {row['filename']}
Resume:
{text}
--------------------
"""

# -----------------------------
# Prompt (STRICT JSON)
# -----------------------------
prompt = PromptTemplate(
    input_variables=["resumes", "query"],
    template="""
You are an AI recruiter.

Below are multiple resumes.
{resumes}

User query:
{query}

TASK:
- Identify resumes relevant to the query
- Return ONLY valid JSON (no markdown, no explanation)

FORMAT:
{{
  "results": [
    {{
      "filename": "Document4.docx",
      "score": 85,
      "justification": "2–4 sentences explaining skills, experience, and why this resume matches the query.",
      "missing_skills": ["Kubernetes", "Terraform"],
      "auto_screen": "Selected"
    }}
  ]
}}

If no resumes match:
{{
  "results": []
}}
"""
)

# -----------------------------
# LLM guard + search
# -----------------------------
if not st.session_state.get("llm_configured"):
    st.error("⚠️ Please configure an LLM provider in the sidebar before searching.")
    st.stop()

try:
    llm = get_llm(temperature=0)
    chain = prompt | llm | StrOutputParser()

    with st.spinner("🔍 Searching resumes using AI reasoning..."):
        raw_result = chain.invoke(
            {
                "resumes": resumes_text,
                "query": query
            }
        )
except Exception as e:
    st.error(f"❌ LLM Error: {e}")
    st.stop()

# -----------------------------
# Parse output
# -----------------------------
st.markdown("---")
st.subheader("Search Results")

try:
    parsed = json.loads(extract_json(raw_result))
except json.JSONDecodeError:
    st.error("❌ Failed to parse LLM output")
    st.text(raw_result)
    st.stop()

results = parsed.get("results", [])

if not results:
    st.info("No matching resumes found.")
    st.stop()

# -----------------------------
# Render results with download
# -----------------------------
for item in results:
    filename = item["filename"]
    justification = item["justification"]
    score = item.get("score", 0)
    missing_skills = item.get("missing_skills", [])
    decision = item.get("auto_screen", "Rejected")

    file_path = os.path.join(RESUME_DIR, filename)

    st.markdown(f"### 📄 {filename}")
    st.write(justification)

    # ---- Metrics Row ----
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Match Score", f"{score}/100")

    with col2:
        if missing_skills:
            st.write("**Skill Gaps:**")
            for skill in missing_skills:
                st.write(f"- {skill}")
        else:
            st.write("**Skill Gaps:** None")

    with col3:
        if decision.lower() == "selected":
            st.success("✅ Auto Screen: Selected")
        else:
            st.error("❌ Auto Screen: Rejected")

    # ---- Download ----
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            st.download_button(
                label="⬇️ Download Resume",
                data=f,
                file_name=filename,
                mime="application/octet-stream",
                key=filename
            )
    else:
        st.warning("⚠️ Resume file not found on server")

    st.divider()

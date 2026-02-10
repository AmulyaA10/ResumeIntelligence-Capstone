"""
JD-Resume Matching & Ranking Dashboard
"""

import streamlit as st
import pandas as pd
from services.matching_workflow import match_resumes_to_jd
from services.resume_parser import extract_text
import os
import tempfile

st.title("🎯 JD-Resume Matching & Ranking")
st.caption("Explainable, evidence-based candidate screening with 100-point rubric scoring.")

st.markdown("---")

# ===== SECTION 1: JD Input =====
st.header("1️⃣ Job Description")

jd_input_method = st.radio(
    "How would you like to provide the JD?",
    ["Paste Text", "Upload File"],
    horizontal=True
)

jd_text = ""

if jd_input_method == "Paste Text":
    jd_text = st.text_area(
        "Paste Job Description",
        height=200,
        placeholder="Paste the full job description here..."
    )
else:
    jd_file = st.file_uploader(
        "Upload Job Description (PDF/DOCX/TXT)",
        type=["pdf", "docx", "txt"]
    )

    if jd_file:
        # Save temporarily and extract text (cross-platform temp file)
        suffix = os.path.splitext(jd_file.name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(jd_file.getbuffer())
            temp_path = tmp.name

        try:
            if jd_file.name.endswith(".txt"):
                with open(temp_path, "r", encoding="utf-8") as f:
                    jd_text = f.read()
            else:
                jd_text = extract_text(temp_path)

            st.success(f"✅ Loaded JD from {jd_file.name}")
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

st.markdown("---")

# ===== SECTION 2: Resume Input =====
st.header("2️⃣ Candidate Resumes")

resume_input_method = st.radio(
    "How would you like to provide resumes?",
    ["Upload Files", "Load from Database", "Paste Text (Multiple)"],
    horizontal=True
)

resume_texts = []

if resume_input_method == "Upload Files":
    resume_files = st.file_uploader(
        "Upload Resumes (PDF/DOCX)",
        type=["pdf", "docx"],
        accept_multiple_files=True
    )

    if resume_files:
        for resume_file in resume_files:
            # Create cross-platform temp file
            suffix = os.path.splitext(resume_file.name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(resume_file.getbuffer())
                temp_path = tmp.name

            try:
                text = extract_text(temp_path)
                resume_texts.append(text)
            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

        st.success(f"✅ Loaded {len(resume_texts)} resumes")

elif resume_input_method == "Load from Database":
    from services.db.lancedb_client import get_or_create_table

    try:
        table = get_or_create_table()
        df = table.to_pandas()

        if not df.empty:
            resume_texts = df["text"].tolist()
            st.success(f"✅ Loaded {len(resume_texts)} resumes from database")
        else:
            st.warning("No resumes found in database. Please upload resumes first.")
    except Exception as e:
        st.error(f"Error loading from database: {e}")

else:  # Paste Text
    num_resumes = st.number_input(
        "How many resumes to paste?",
        min_value=1,
        max_value=10,
        value=2
    )

    for i in range(num_resumes):
        resume_text = st.text_area(
            f"Resume {i + 1}",
            height=150,
            key=f"resume_{i}",
            placeholder=f"Paste resume {i + 1} here..."
        )
        if resume_text.strip():
            resume_texts.append(resume_text)

st.markdown("---")

# ===== SECTION 3: Scoring Options =====
st.header("3️⃣ Scoring Options")

col1, col2 = st.columns(2)

with col1:
    score_threshold = st.slider(
        "Minimum Score Filter",
        min_value=0,
        max_value=100,
        value=60,
        help="Show only candidates with scores >= this threshold"
    )

with col2:
    show_recommendation = st.multiselect(
        "Filter by Recommendation",
        ["Shortlist", "Review", "Reject"],
        default=["Shortlist", "Review"],
        help="Filter candidates by recommendation type"
    )

st.markdown("---")

# ===== SECTION 4: Run Matching =====
if st.button("🚀 Run Matching & Ranking", type="primary", use_container_width=True):
    # LLM guard
    if not st.session_state.get("llm_configured"):
        st.error("⚠️ Please configure an LLM provider in the sidebar before running matching.")
        st.stop()

    # Input validation
    if not jd_text.strip():
        st.error("❌ Please provide a job description")
        st.stop()

    if len(resume_texts) == 0:
        st.error("❌ Please provide at least one resume")
        st.stop()

    # Check for empty resumes
    valid_resumes = [r for r in resume_texts if r.strip()]
    if len(valid_resumes) == 0:
        st.error("❌ All resumes are empty. Please check your input files.")
        st.stop()

    if len(valid_resumes) < len(resume_texts):
        st.warning(f"⚠️ Skipping {len(resume_texts) - len(valid_resumes)} empty resume(s)")
        resume_texts = valid_resumes

    with st.spinner(f"🔄 Processing JD + {len(resume_texts)} resumes..."):
        try:
            result = match_resumes_to_jd(jd_text, resume_texts)

            st.session_state["matching_result"] = result
            st.success(f"✅ Matching complete! Processed {result['total_candidates']} candidates")

        except ValueError as e:
            st.error(f"Configuration Error: {e}")
            st.stop()

        except Exception as e:
            st.error(f"Error during matching: {e}")
            with st.expander("View error details"):
                st.exception(e)
            st.stop()

st.markdown("---")

# ===== SECTION 5: Results Display =====
if "matching_result" in st.session_state:
    result = st.session_state["matching_result"]
    ranked_candidates = result["ranked_candidates"]
    jd_requirements = result["jd_requirements"]

    st.header("📊 Results")

    # Display JD requirements summary
    with st.expander("🔍 Job Requirements Summary", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Must-Have Skills")
            for skill in jd_requirements.get("must_have_skills", []):
                st.markdown(f"- {skill}")

        with col2:
            st.subheader("Requirements")
            st.write(f"**Experience:** {jd_requirements.get('years_of_experience', {}).get('total', 0)} years")
            st.write(f"**Seniority:** {jd_requirements.get('role_seniority', 'N/A')}")
            st.write(f"**Domain:** {', '.join(jd_requirements.get('domain_keywords', [])[:3])}")

    st.markdown("---")

    # Filter candidates
    filtered_candidates = [
        c for c in ranked_candidates
        if c["final_score"] >= score_threshold and c["recommendation"] in show_recommendation
    ]

    st.subheader(f"🏆 Candidate Ranking ({len(filtered_candidates)} candidates)")

    if not filtered_candidates:
        st.warning("No candidates match the current filters. Try adjusting the threshold or recommendation filters.")
        st.stop()

    # Create ranking table
    table_data = []
    for candidate in filtered_candidates:
        score_result = candidate["score_result"]
        breakdown = score_result["breakdown"]

        table_data.append({
            "Rank": candidate["rank"],
            "Candidate": candidate["candidate_id"],
            "Score": f"{candidate['final_score']}/100",
            "Recommendation": candidate["recommendation"],
            "Skills Match": f"{len(breakdown['skill_coverage']['matched_skills'])}/{len(breakdown['skill_coverage']['matched_skills']) + len(breakdown['skill_coverage']['missing_skills'])}",
            "Experience": f"{breakdown['experience_depth']['resume_years']} yrs",
            "Penalties": f"-{score_result['penalty']} pts",
            "Summary": candidate["summary"]
        })

    df = pd.DataFrame(table_data)

    # Style the table
    def highlight_recommendation(row):
        if row["Recommendation"] == "Shortlist":
            return ["background-color: #d4edda"] * len(row)
        elif row["Recommendation"] == "Review":
            return ["background-color: #fff3cd"] * len(row)
        else:
            return ["background-color: #f8d7da"] * len(row)

    styled_df = df.style.apply(highlight_recommendation, axis=1)

    st.dataframe(styled_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Detailed candidate views
    st.subheader("📋 Detailed Candidate Reports")

    for candidate in filtered_candidates:
        with st.expander(
            f"🔍 {candidate['candidate_id']} - Score: {candidate['final_score']}/100 - {candidate['recommendation']}",
            expanded=False
        ):
            # Display explanation in markdown
            st.markdown(candidate["explanation"])

            # Show score breakdown chart
            st.subheader("Score Breakdown Chart")

            breakdown = candidate["score_result"]["breakdown"]

            chart_data = pd.DataFrame({
                "Component": [
                    "Skill Coverage",
                    "Experience Depth",
                    "Domain Relevance",
                    "Evidence Quality",
                    "Quantification",
                    "Recency"
                ],
                "Score": [
                    breakdown["skill_coverage"]["score"],
                    breakdown["experience_depth"]["score"],
                    breakdown["domain_relevance"]["score"],
                    breakdown["evidence_quality"]["score"],
                    breakdown["quantification"]["score"],
                    breakdown["recency"]["score"]
                ],
                "Max": [30, 20, 15, 15, 10, 10]
            })

            st.bar_chart(chart_data.set_index("Component")[["Score", "Max"]])

    st.markdown("---")

    # Export options
    st.subheader("📥 Export Results")

    col1, col2 = st.columns(2)

    with col1:
        # Export ranking table as CSV
        csv = df.to_csv(index=False)
        st.download_button(
            label="⬇️ Download Ranking Table (CSV)",
            data=csv,
            file_name="candidate_ranking.csv",
            mime="text/csv"
        )

    with col2:
        # Export shortlisted candidates
        shortlisted = [c for c in filtered_candidates if c["recommendation"] == "Shortlist"]

        if shortlisted:
            shortlist_data = [
                {
                    "Candidate": c["candidate_id"],
                    "Score": c["final_score"],
                    "Summary": c["summary"]
                }
                for c in shortlisted
            ]

            shortlist_df = pd.DataFrame(shortlist_data)
            shortlist_csv = shortlist_df.to_csv(index=False)

            st.download_button(
                label=f"⬇️ Download Shortlist ({len(shortlisted)} candidates)",
                data=shortlist_csv,
                file_name="shortlisted_candidates.csv",
                mime="text/csv"
            )
        else:
            st.info("No candidates to shortlist with current filters")

else:
    st.info("👆 Configure JD and resumes above, then click 'Run Matching & Ranking' to see results")

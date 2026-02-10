import streamlit as st
from services.agent_controller import run_resume_pipeline

st.title("🧠 Skill Gap Analysis")
st.caption("Compare candidate skills against job requirements using LangGraph agents.")

col1, col2 = st.columns(2)

with col1:
    resume_text = st.text_area(
        "📄 Candidate Resume",
        height=300,
        placeholder="Paste resume text here..."
    )

with col2:
    jd_text = st.text_area(
        "📋 Job Description",
        height=300,
        placeholder="Paste job description here..."
    )

st.markdown("---")

if st.button("Analyze Skill Gaps", type="primary"):
    if not resume_text.strip() or not jd_text.strip():
        st.warning("Please provide both resume and job description")
    elif not st.session_state.get("llm_configured"):
        st.error("⚠️ Please configure an LLM provider in the sidebar before analyzing.")
    else:
        try:
            with st.spinner("Running skill gap agent..."):
                output = run_resume_pipeline(
                    task="skill_gap",
                    resumes=[resume_text],
                    query=jd_text
                )

            gaps = output["gaps"]

            col_a, col_b = st.columns(2)

            with col_a:
                st.subheader("Missing Skills")
                for skill in gaps["missing_skills"]:
                    st.error(skill)

            with col_b:
                st.subheader("Recommended to Learn")
                for skill in gaps["recommended"]:
                    st.success(skill)
        except Exception as e:
            st.error(f"❌ Error: {e}")

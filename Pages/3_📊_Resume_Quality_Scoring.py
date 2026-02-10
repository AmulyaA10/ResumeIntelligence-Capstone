import streamlit as st
from services.agent_controller import run_resume_pipeline

st.title("📊 Resume Quality Scoring")
st.caption("LangGraph agent evaluates resume structure, completeness, and presentation.")

resume_text = st.text_area(
    "Paste Resume Text",
    height=300,
    placeholder="Paste candidate resume here..."
)

st.markdown("---")

if st.button("Score Resume", type="primary"):
    if not resume_text.strip():
        st.warning("Please paste resume text")
    elif not st.session_state.get("llm_configured"):
        st.error("⚠️ Please configure an LLM provider in the sidebar before scoring.")
    else:
        try:
            with st.spinner("Running quality scoring agent..."):
                output = run_resume_pipeline(
                    task="score",
                    resumes=[resume_text]
                )

            score = output["score"]["overall"]

            st.metric("Overall Resume Score", score)

            st.subheader("Score Breakdown")
            st.json(output["score"])
        except Exception as e:
            st.error(f"❌ Error: {e}")

import streamlit as st
from services.agent_controller import run_resume_pipeline

st.title("🤖 Auto Screening")
st.caption("Automated pass / reject decision based on LangGraph quality scoring.")

resume_text = st.text_area(
    "Candidate Resume",
    height=300,
    placeholder="Paste resume text here..."
)

threshold = st.slider(
    "Selection Threshold",
    min_value=50,
    max_value=90,
    value=75,
    help="Candidates scoring above this threshold are selected."
)

st.markdown("---")

if st.button("Run Auto Screening", type="primary"):
    if not resume_text.strip():
        st.warning("Please paste resume text")
    elif not st.session_state.get("llm_configured"):
        st.error("⚠️ Please configure an LLM provider in the sidebar before screening.")
    else:
        try:
            with st.spinner("Executing agent workflow..."):
                output = run_resume_pipeline(
                    task="screen",
                    resumes=[resume_text]
                )

            decision = output["decision"]
            score = output["score"]["overall"]

            col_a, col_b = st.columns([1, 2])

            with col_a:
                st.metric("Score", f"{score}/100")
                if decision["selected"]:
                    st.success("✅ Selected")
                else:
                    st.error("❌ Rejected")

            with col_b:
                st.subheader("Reasoning")
                st.write(decision["reason"])
        except Exception as e:
            st.error(f"❌ Error: {e}")

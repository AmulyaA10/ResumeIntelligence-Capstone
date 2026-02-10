import streamlit as st
from services.agent_controller import generate_resume_from_linkedin

st.title("🔗 LinkedIn to Resume")
st.caption("Generate a professional resume from a LinkedIn profile URL using LangGraph agents.")

linkedin_url = st.text_input(
    "LinkedIn Profile URL",
    placeholder="https://www.linkedin.com/in/username"
)

st.markdown("---")

if st.button("Generate Resume", type="primary"):
    if not linkedin_url.strip():
        st.warning("Please enter a LinkedIn URL.")
    elif not st.session_state.get("llm_configured"):
        st.error("⚠️ Please configure an LLM provider in the sidebar before generating.")
    else:
        with st.spinner("Generating resume from LinkedIn profile..."):
            try:
                output = generate_resume_from_linkedin(linkedin_url)

                st.subheader("Generated Resume")
                st.text_area(
                    "Resume",
                    output["resume"],
                    height=500,
                )

                st.download_button(
                    label="Download as Text",
                    data=output["resume"],
                    file_name="linkedin_resume.txt",
                    mime="text/plain",
                )
            except Exception as e:
                st.error(f"Error: {e}")

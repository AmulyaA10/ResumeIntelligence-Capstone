import streamlit as st
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from services.llm_config import get_llm

st.title("📝 Resume Generator")
st.caption("AI-generated ATS-optimized resume from your profile description.")

profile = st.text_area(
    "Describe yourself",
    height=200,
    placeholder="I am a data scientist with 3 years experience in Python, ML, and NLP. "
    "I worked at XYZ Corp building recommendation systems..."
)

target_role = st.text_input(
    "Target Role (optional)",
    placeholder="e.g. Senior Data Scientist"
)

st.markdown("---")

if st.button("Generate Resume", type="primary"):
    if not profile.strip():
        st.warning("Please describe your background")
    elif not st.session_state.get("llm_configured"):
        st.error("⚠️ Please configure an LLM provider in the sidebar before generating.")
    else:
        try:
            prompt = PromptTemplate(
                input_variables=["profile", "target_role"],
                template="""
You are a professional resume writer creating ATS-friendly resumes.

Candidate Profile:
{profile}

Target Role: {target_role}

TASK:
Create a clean, professional, ATS-optimized resume using the provided information.

RULES:
- Use a clear structure: Name, Summary, Experience, Skills, Education
- Use bullet points with action verbs for experience
- Quantify achievements where possible
- Keep it concise (one page equivalent)
- Professional tone throughout
- If target role is specified, tailor the resume towards that role

Return the resume in clean text format.
"""
            )

            llm = get_llm(temperature=0.3)
            chain = prompt | llm | StrOutputParser()

            with st.spinner("Generating your resume..."):
                result = chain.invoke({
                    "profile": profile,
                    "target_role": target_role or "Not specified"
                })

                st.subheader("Generated Resume")
                st.text_area(
                    "Your Resume",
                    result,
                    height=500
                )

                st.download_button(
                    label="⬇️ Download as Text",
                    data=result,
                    file_name="generated_resume.txt",
                    mime="text/plain"
                )
        except Exception as e:
            st.error(f"❌ Error: {e}")

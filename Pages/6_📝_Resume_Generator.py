import streamlit as st

st.header("📝 Resume Generator")

profile = st.text_area(
    "Describe yourself",
    placeholder="I am a data scientist with 3 years experience..."
)

if st.button("✨ Generate Resume"):
    st.subheader("Generated Resume")
    st.code("Generated resume content goes here...")

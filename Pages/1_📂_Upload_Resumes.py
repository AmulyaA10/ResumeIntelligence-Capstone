import streamlit as st
import os
from pathlib import Path
from services.resume_parser import extract_text
from services.db.lancedb_client import store_resume

PROJECT_ROOT = Path(__file__).resolve().parent.parent
UPLOAD_DIR = str(PROJECT_ROOT / "data" / "raw_resumes")
os.makedirs(UPLOAD_DIR, exist_ok=True)

st.title("📂 Upload Resumes")
st.caption("Upload PDF or DOCX files to parse and store in the vector database.")

st.markdown("---")

files = st.file_uploader(
    "Select resume files",
    type=["pdf", "docx"],
    accept_multiple_files=True,
)

store_db = st.checkbox("Store in Vector Database (LanceDB)", value=True)

if st.button("Process Resumes", type="primary"):
    if not files:
        st.warning("Please upload at least one resume.")
    else:
        progress = st.progress(0, text="Processing...")
        success_count = 0
        for idx, file in enumerate(files):
            file_path = os.path.join(UPLOAD_DIR, file.name)

            try:
                with open(file_path, "wb") as f:
                    f.write(file.getbuffer())

                text = extract_text(file_path)

                if store_db:
                    store_resume(file.name, text)

                success_count += 1
            except Exception as e:
                st.error(f"❌ Failed to process {file.name}: {e}")

            progress.progress((idx + 1) / len(files), text=f"Processed {file.name}")

        progress.empty()
        if success_count > 0:
            st.success(f"Processed {success_count} of {len(files)} resume(s) successfully.")
            if store_db:
                st.info(f"{success_count} resumes indexed in LanceDB.")


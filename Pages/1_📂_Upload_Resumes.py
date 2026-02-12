import streamlit as st
import os
import tempfile
from pathlib import Path
from services.resume_parser import extract_text
from services.db.lancedb_client import store_resume, is_duplicate, extract_signals_if_llm_ready

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
        dup_count = 0
        signals_count = 0
        for idx, file in enumerate(files):
            try:
                # Extract text from temp file first (before committing to disk)
                suffix = os.path.splitext(file.name)[1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(file.getbuffer())
                    tmp_path = tmp.name

                text = extract_text(tmp_path)
                os.unlink(tmp_path)

                # Check for duplicate content before saving anything
                if store_db and is_duplicate(text):
                    dup_count += 1
                    st.warning(f"⚠️ {file.name} — duplicate content, skipped.")
                else:
                    # Save file to disk
                    file_path = os.path.join(UPLOAD_DIR, file.name)
                    with open(file_path, "wb") as f:
                        f.write(file.getbuffer())

                    # Index in LanceDB (with cached signals if LLM is ready)
                    if store_db:
                        progress.progress(
                            (idx + 0.5) / len(files),
                            text=f"Extracting signals for {file.name}..."
                        )
                        signals = extract_signals_if_llm_ready(text)
                        store_resume(file.name, text, signals=signals)
                        if signals:
                            signals_count += 1

                    success_count += 1
            except Exception as e:
                st.error(f"❌ Failed to process {file.name}: {e}")

            progress.progress((idx + 1) / len(files), text=f"Processed {file.name}")

        progress.empty()
        if success_count > 0:
            st.success(f"Processed {success_count} of {len(files)} resume(s) successfully.")
            if store_db:
                st.info(f"{success_count} resumes indexed in LanceDB.")
                if signals_count > 0:
                    st.info(f"⚡ {signals_count} resume(s) pre-analyzed — matching will be faster.")
                elif signals_count == 0 and success_count > 0:
                    st.caption("💡 Configure an LLM in the sidebar to pre-analyze resumes at upload time for faster matching.")
        if dup_count > 0:
            st.info(f"🔁 {dup_count} duplicate(s) skipped.")


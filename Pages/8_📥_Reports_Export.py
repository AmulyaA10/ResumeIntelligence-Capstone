import streamlit as st
import pandas as pd
from services.db.lancedb_client import get_or_create_table

st.title("📥 Reports & Export")
st.caption("Download stored resume data and matching results as CSV.")

st.markdown("---")

st.subheader("Stored Resumes")

try:
    table = get_or_create_table()
    df = table.to_pandas()

    if not df.empty:
        st.info(f"Found {len(df)} resumes in database")

        export_format = st.selectbox("Export Format", ["CSV"])

        if st.button("⬇️ Export Resume Database"):
            export_df = df[["id", "filename", "text"]].copy()
            # Truncate text for readability in CSV
            export_df["text_preview"] = export_df["text"].str[:500] + "..."

            csv_data = export_df[["id", "filename", "text_preview"]].to_csv(index=False)
            st.download_button(
                label="⬇️ Download CSV",
                data=csv_data,
                file_name="resumes_export.csv",
                mime="text/csv"
            )
    else:
        st.warning("No resumes found in database. Upload resumes first on the Upload page.")
except Exception as e:
    st.error(f"Error loading database: {e}")

st.markdown("---")

st.subheader("Matching Results")

if "matching_result" in st.session_state:
    result = st.session_state["matching_result"]
    ranked_candidates = result["ranked_candidates"]

    st.success(f"Found matching results for {len(ranked_candidates)} candidates")

    table_data = []
    for candidate in ranked_candidates:
        score_result = candidate["score_result"]
        breakdown = score_result["breakdown"]

        table_data.append({
            "Rank": candidate["rank"],
            "Candidate": candidate["candidate_id"],
            "Final Score": candidate["final_score"],
            "Recommendation": candidate["recommendation"],
            "Skills Matched": len(breakdown["skill_coverage"]["matched_skills"]),
            "Skills Missing": len(breakdown["skill_coverage"]["missing_skills"]),
            "Experience (yrs)": breakdown["experience_depth"]["resume_years"],
            "Penalty": score_result["penalty"],
            "Summary": candidate["summary"]
        })

    results_df = pd.DataFrame(table_data)
    st.dataframe(results_df, use_container_width=True, hide_index=True)

    csv_data = results_df.to_csv(index=False)
    st.download_button(
        label="⬇️ Download Matching Results (CSV)",
        data=csv_data,
        file_name="matching_results.csv",
        mime="text/csv"
    )
else:
    st.info("No matching results available. Run JD-Resume Matching first on the Matching page.")

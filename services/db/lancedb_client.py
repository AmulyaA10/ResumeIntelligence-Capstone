import lancedb
import hashlib
import json
from pathlib import Path
from uuid import uuid4
import pyarrow as pa

# ---------- DB PATH ----------
# Use path relative to project root (parent of services/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT_ROOT / "data" / "lancedb"
DB_PATH.mkdir(parents=True, exist_ok=True)

db = lancedb.connect(DB_PATH)

# ---------- SCHEMA ----------
resume_schema = pa.schema([
    pa.field("id", pa.string()),
    pa.field("filename", pa.string()),
    pa.field("text", pa.string()),
    pa.field("fingerprint", pa.string()),
    pa.field("signals", pa.string()),  # JSON-serialized structured signals (cached)
])

# ---------- FINGERPRINT ----------
def generate_fingerprint(text: str) -> str:
    """SHA-256 fingerprint of normalized resume text for dedup."""
    normalized = " ".join(text.split()).lower()
    return hashlib.sha256(normalized.encode()).hexdigest()

# ---------- TABLE HANDLER ----------
def get_or_create_table():
    if "resumes" in db.table_names():
        table = db.open_table("resumes")
        current_cols = table.schema.names
        needs_migration = False

        # Migrate old tables that lack required columns
        if "fingerprint" not in current_cols or "signals" not in current_cols:
            needs_migration = True

        if needs_migration:
            df = table.to_pandas()
            if "fingerprint" not in df.columns:
                df["fingerprint"] = df["text"].apply(generate_fingerprint)
            if "signals" not in df.columns:
                df["signals"] = ""  # Empty string = not yet extracted
            db.drop_table("resumes")
            return db.create_table(
                name="resumes",
                data=df[["id", "filename", "text", "fingerprint", "signals"]],
                schema=resume_schema,
                mode="create"
            )

        return table

    return db.create_table(
        name="resumes",
        schema=resume_schema,
        mode="create"
    )

# ---------- DUPLICATE CHECK ----------
def is_duplicate(text: str) -> bool:
    """Check if resume content already exists in the database."""
    table = get_or_create_table()
    fp = generate_fingerprint(text)
    df = table.to_pandas()
    if "fingerprint" in df.columns and not df.empty:
        return fp in df["fingerprint"].values
    return False

# ---------- STORE ----------
def store_resume(filename: str, text: str, signals: dict = None) -> str:
    """
    Store a resume in LanceDB with duplicate detection.

    Args:
        filename: Original file name
        text: Raw resume text
        signals: Pre-extracted structured signals (dict). If None, stored empty for lazy extraction.

    Returns:
        "stored" if new resume was added
        "duplicate" if resume content already exists
    """
    table = get_or_create_table()
    fp = generate_fingerprint(text)

    # Check for duplicate fingerprint
    df = table.to_pandas()
    if "fingerprint" in df.columns and not df.empty:
        if fp in df["fingerprint"].values:
            return "duplicate"

    # Serialize signals to JSON string (empty string if not provided)
    signals_json = json.dumps(signals) if signals else ""

    table.add([{
        "id": str(uuid4()),
        "filename": filename,
        "text": text,
        "fingerprint": fp,
        "signals": signals_json
    }])
    return "stored"


# ---------- RETRIEVE CACHED SIGNALS ----------
def get_cached_signals(text: str):
    """
    Retrieve cached signals for a resume by its text fingerprint.

    Args:
        text: Raw resume text

    Returns:
        Parsed signals dict if cached, None if not available
    """
    table = get_or_create_table()
    fp = generate_fingerprint(text)
    df = table.to_pandas()

    if df.empty or "fingerprint" not in df.columns:
        return None

    match = df[df["fingerprint"] == fp]
    if match.empty:
        return None

    signals_json = match.iloc[0].get("signals", "")
    if not signals_json or signals_json.strip() == "":
        return None

    try:
        return json.loads(signals_json)
    except (json.JSONDecodeError, TypeError):
        return None


# ---------- SAFE SIGNAL EXTRACTION ----------
def extract_signals_if_llm_ready(text: str):
    """
    Attempt to extract structured signals via LLM at upload time.
    Returns the signals dict if LLM is configured, None otherwise.
    This ensures uploads work even without an LLM key configured.
    """
    try:
        import streamlit as st
        if not st.session_state.get("llm_configured"):
            return None
    except Exception:
        return None

    try:
        from services.resume_enricher import extract_resume_signals
        return extract_resume_signals(text)
    except Exception:
        # LLM call failed — don't block the upload
        return None

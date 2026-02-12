import lancedb
import hashlib
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

        # Migrate old tables that lack the fingerprint column
        if "fingerprint" not in table.schema.names:
            df = table.to_pandas()
            df["fingerprint"] = df["text"].apply(generate_fingerprint)
            db.drop_table("resumes")
            return db.create_table(
                name="resumes",
                data=df[["id", "filename", "text", "fingerprint"]],
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
def store_resume(filename: str, text: str) -> str:
    """
    Store a resume in LanceDB with duplicate detection.

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

    table.add([{
        "id": str(uuid4()),
        "filename": filename,
        "text": text,
        "fingerprint": fp
    }])
    return "stored"

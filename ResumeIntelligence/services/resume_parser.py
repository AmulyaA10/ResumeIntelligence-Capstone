from pypdf import PdfReader
import docx
import os


def extract_text(file_path: str) -> str:
    """
    Extract text from PDF or DOCX files.

    Args:
        file_path: Path to the resume file

    Returns:
        Extracted text content

    Raises:
        FileNotFoundError: If file does not exist
        ValueError: If file type is not supported
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if file_path.endswith(".pdf"):
        reader = PdfReader(file_path)
        text = "\n".join(p.extract_text() or "" for p in reader.pages)
        return text.strip()

    if file_path.endswith(".docx"):
        doc = docx.Document(file_path)
        text = "\n".join(p.text for p in doc.paragraphs)
        return text.strip()

    raise ValueError(f"Unsupported file type: {os.path.splitext(file_path)[1]}. Only .pdf and .docx are supported.")

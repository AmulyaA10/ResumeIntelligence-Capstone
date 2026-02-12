# Setup Guide - Resume Intelligence Platform

Step-by-step instructions to get the application running on your machine.

---

## Prerequisites

- **Python 3.9+** installed ([python.org](https://www.python.org/downloads/))
- **pip** (comes with Python)
- An **API key** from any supported LLM provider (see Step 4)

---

## Step 1: Clone or Download the Project

```bash
# If cloning from git:
git clone <your-repo-url>
cd ResumeIntelligence

# Or if you have the folder already:
cd /path/to/ResumeIntelligence
```

---

## Step 2: Create a Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
# macOS / Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

---

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs: Streamlit, LangGraph, LangChain, LanceDB, PyPDF, python-docx, and all LLM provider libraries.

**What gets installed:**

| Package             | Purpose                          |
|---------------------|----------------------------------|
| streamlit           | Web UI framework                 |
| langgraph           | Agentic workflow orchestration   |
| langchain-core      | LLM abstraction layer            |
| langchain-openai    | OpenAI + OpenRouter support      |
| langchain-anthropic | Claude support                   |
| langchain-google-genai | Gemini support                |
| langchain-groq      | Groq support                     |
| lancedb             | Vector database                  |
| pypdf               | PDF text extraction              |
| python-docx         | DOCX text extraction             |
| pandas              | Data processing                  |

---

## Step 4: Get an API Key

You need an API key from **any one** of these providers:

| Provider                  | Get Key From                          | Cost       |
|---------------------------|---------------------------------------|------------|
| **OpenRouter (Free)**     | https://openrouter.ai/keys            | Free tier available |
| **Groq**                  | https://console.groq.com/keys         | Free tier available |
| **Google Gemini**         | https://aistudio.google.com/apikey    | Free tier available |
| **OpenAI**                | https://platform.openai.com/api-keys  | Paid       |
| **Anthropic (Claude)**    | https://console.anthropic.com/        | Paid       |

**Recommendation for testing:** Use **OpenRouter** or **Groq** (both have free tiers).

---

## Step 5: Run the Application

```bash
streamlit run Home.py
```

The app opens in your browser at **http://localhost:8501**.

---

## Step 6: Configure LLM in the Sidebar

1. In the **sidebar** (left side), find **LLM Configuration**
2. Select your **Provider** (e.g., "Free Models (OpenRouter)")
3. Paste your **API Key**
4. Select a **Model** (default is pre-selected)
5. You should see a green checkmark: **"Provider / model-name"**

---

## Step 7: Start Using Features

### Quick Workflow: Upload + Match

1. **Upload Resumes** (Page 1)
   - Click "Upload Resumes" in the sidebar
   - Upload one or more PDF/DOCX resume files
   - Click "Process Resumes"
   - Resumes are parsed and stored in LanceDB

2. **JD-Resume Matching** (Page 9)
   - Click "JD Resume Matching" in the sidebar
   - Paste a job description (or upload a file)
   - Select resumes: "Load from Database" to use uploaded resumes
   - Click "Run Matching & Ranking"
   - View ranked results with scores, explanations, and charts

3. **Export Results** (Page 8)
   - Click "Reports Export" in the sidebar
   - Download ranking table or shortlist as CSV

### Other Features

| Page | What It Does | Input Needed |
|------|-------------|--------------|
| Search Resumes | Semantic search across stored resumes | Search query |
| Quality Scoring | Score a single resume's structure | Paste resume text |
| Skill Gap Analysis | Find missing skills vs. a JD | Paste resume + JD |
| Auto Screening | Pass/reject based on quality score | Paste resume text |
| Resume Generator | AI-writes an ATS-optimized resume | Describe your background |
| LinkedIn to Resume | Generate resume from LinkedIn URL | LinkedIn profile URL |

---

## Troubleshooting

### "No LLM configured" error
- Make sure you selected a provider and entered your API key in the sidebar
- The green checkmark should be visible

### "Module not found" error
- Run `pip install -r requirements.txt` again
- Make sure your virtual environment is activated

### App won't start
- Check you're running `streamlit run Home.py` (not `python Home.py`)
- Make sure you're in the `ResumeIntelligence/` directory

### LLM returns errors
- Check your API key is valid and has credits
- Try a different model (some free models have rate limits)
- Check your internet connection

### PDF/DOCX parsing fails
- Make sure files are not password-protected
- Scanned PDFs (images) won't work — the file must contain actual text

---

## Project Structure Quick Reference

```
ResumeIntelligence/
├── Home.py              # Main entry point (run this)
├── Pages/               # All 9 feature pages
├── services/            # Core AI and scoring logic
│   ├── llm_config.py    # LLM provider configuration
│   ├── matching_workflow.py  # Main matching pipeline
│   └── ...              # Parsers, scorers, explainers
├── data/                # Stored resumes and DB files
└── requirements.txt     # Python dependencies
```

---

## Running Tests

```bash
# Syntax check all files
python3 -c "import ast, pathlib; [ast.parse(f.read_text()) for f in pathlib.Path('.').rglob('*.py')]; print('All files OK')"

# Import check (no API key needed)
python3 -c "from services.llm_config import PROVIDER_MODELS; print(f'{len(PROVIDER_MODELS)} providers available')"

# Scoring pipeline test (no API key needed)
python3 test_matching.py
```

import streamlit as st
from services.llm_config import PROVIDER_MODELS

st.set_page_config(
    page_title="Resume Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }

    /* Tech badges */
    .tech-badge {
        display: inline-block;
        border-radius: 20px;
        padding: 0.3rem 0.85rem;
        font-size: 0.78rem;
        font-weight: 600;
        margin: 0.15rem;
    }
    .badge-langgraph   { background: #dbeafe; color: #1d4ed8; }
    .badge-langchain   { background: #d1fae5; color: #047857; }
    .badge-streamlit   { background: #ffe4e6; color: #be123c; }
    .badge-lancedb     { background: #fef3c7; color: #92400e; }
    .badge-multillm    { background: #ede9fe; color: #6d28d9; }

    /* Subtitle */
    .hero-sub { font-size: 1.05rem; color: #555; margin-bottom: 1.2rem; margin-top: -0.5rem; }

    /* Highlight cards */
    .hl-card {
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #e2e8f0;
        height: 100%;
    }
    .hl-blue   { background: linear-gradient(135deg, #dbeafe, #bfdbfe); }
    .hl-green  { background: linear-gradient(135deg, #d1fae5, #a7f3d0); }
    .hl-amber  { background: linear-gradient(135deg, #fef3c7, #fde68a); }
</style>
""", unsafe_allow_html=True)

# ── Sidebar: LLM Configuration (below auto page-nav) ───────────────
st.sidebar.markdown("---")
st.sidebar.markdown("#### ⚙️ LLM Configuration")

for key, default in [
    ("llm_provider", None),
    ("llm_api_key", ""),
    ("llm_model", None),
    ("llm_configured", False),
]:
    if key not in st.session_state:
        st.session_state[key] = default

provider_names = list(PROVIDER_MODELS.keys())

selected_provider = st.sidebar.selectbox(
    "Provider",
    options=provider_names,
    index=None,
    placeholder="Select a provider...",
)

if selected_provider:
    provider_config = PROVIDER_MODELS[selected_provider]

    api_key = st.sidebar.text_input(
        "API Key",
        type="password",
        placeholder="Paste your API key...",
    )

    available_models = provider_config["models"]
    default_model = provider_config["default_model"]
    default_idx = (
        available_models.index(default_model)
        if default_model in available_models
        else 0
    )

    selected_model = st.sidebar.selectbox(
        "Model",
        options=available_models,
        index=default_idx,
    )

    if api_key:
        st.session_state["llm_provider"] = selected_provider
        st.session_state["llm_api_key"] = api_key
        st.session_state["llm_model"] = selected_model
        st.session_state["llm_configured"] = True
        st.sidebar.success(f"✅ {selected_provider} · {selected_model}")
    else:
        st.sidebar.warning("Enter API key to activate")
else:
    if st.session_state.get("llm_configured"):
        p = st.session_state["llm_provider"]
        m = st.session_state["llm_model"]
        st.sidebar.success(f"✅ {p} · {m}")
    else:
        st.sidebar.info("Select a provider to get started")

# ── Hero Section ────────────────────────────────────────────────────
st.title("🧠 Resume Intelligence Platform")
st.markdown(
    '<p class="hero-sub">AI-powered resume screening, scoring & candidate ranking with LangGraph agentic workflows.</p>',
    unsafe_allow_html=True,
)

# Tech stack badges (colored)
st.markdown(
    '<span class="tech-badge badge-langgraph">LangGraph</span>'
    '<span class="tech-badge badge-langchain">LangChain</span>'
    '<span class="tech-badge badge-streamlit">Streamlit</span>'
    '<span class="tech-badge badge-lancedb">LanceDB</span>'
    '<span class="tech-badge badge-multillm">Multi-LLM</span>',
    unsafe_allow_html=True,
)

st.markdown("")

# ── LLM Status Banner ──────────────────────────────────────────────
if not st.session_state.get("llm_configured"):
    st.warning(
        "**Get started** — select an LLM provider and enter your API key in the sidebar to enable AI features."
    )

st.markdown("---")

# ── How It Works ────────────────────────────────────────────────────
st.subheader("How It Works")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        '<div class="hl-card hl-blue">'
        "<h4>1. Upload</h4>"
        "<p>Upload PDF / DOCX resumes. They're parsed and stored in LanceDB for fast retrieval.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        '<div class="hl-card hl-green">'
        "<h4>2. Provide JD</h4>"
        "<p>Paste or upload a job description. The LLM extracts must-have skills, experience, and domain.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        '<div class="hl-card hl-amber">'
        "<h4>3. Match & Rank</h4>"
        "<p>LangGraph agents score each candidate on a 100-point rubric and rank them with explanations.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

st.markdown("")
st.markdown("Navigate to any feature using the **sidebar menu** on the left.")

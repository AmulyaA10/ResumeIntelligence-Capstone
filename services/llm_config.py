"""
Shared LLM configuration module.
Supports multiple providers via Streamlit session_state sidebar UI.
"""

import re

# ---------------------------------------------------------------------------
# Provider / model registry
# ---------------------------------------------------------------------------
PROVIDER_MODELS = {
    "OpenAI": {
        "models": [
            "gpt-4o-mini",
            "gpt-4o",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
        ],
        "default_model": "gpt-4o-mini",
        "class": "ChatOpenAI",
        "kwargs": {},
    },
    "Anthropic (Claude)": {
        "models": [
            "claude-sonnet-4-20250514",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
        ],
        "default_model": "claude-sonnet-4-20250514",
        "class": "ChatAnthropic",
        "kwargs": {},
    },
    "Google Gemini": {
        "models": [
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
        ],
        "default_model": "gemini-2.0-flash",
        "class": "ChatGoogleGenerativeAI",
        "kwargs": {},
    },
    "Groq": {
        "models": [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
        ],
        "default_model": "llama-3.3-70b-versatile",
        "class": "ChatGroq",
        "kwargs": {},
    },
    "OpenRouter": {
        "models": [
            "openai/gpt-4o-mini",
            "anthropic/claude-3.5-sonnet",
            "google/gemini-2.0-flash-exp:free",
            "meta-llama/llama-3.3-70b-instruct:free",
            "mistralai/mistral-7b-instruct:free",
            "qwen/qwen-2.5-72b-instruct:free",
        ],
        "default_model": "meta-llama/llama-3.3-70b-instruct:free",
        "class": "ChatOpenAI",
        "kwargs": {"base_url": "https://openrouter.ai/api/v1"},
    },
    "Free Models (OpenRouter)": {
        "models": [
            "google/gemini-2.0-flash-exp:free",
            "meta-llama/llama-3.3-70b-instruct:free",
            "mistralai/mistral-7b-instruct:free",
            "qwen/qwen-2.5-72b-instruct:free",
            "huggingfaceh4/zephyr-7b-beta:free",
        ],
        "default_model": "meta-llama/llama-3.3-70b-instruct:free",
        "class": "ChatOpenAI",
        "kwargs": {"base_url": "https://openrouter.ai/api/v1"},
    },
}


# ---------------------------------------------------------------------------
# JSON extraction helper (non-OpenAI models often wrap JSON in code fences)
# ---------------------------------------------------------------------------
def extract_json(text: str) -> str:
    """Strip markdown code fences from LLM output if present."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        return match.group(1).strip()
    return text


# ---------------------------------------------------------------------------
# Core factory
# ---------------------------------------------------------------------------
def get_llm(temperature: float = 0, model: str = None):
    """
    Create a chat model instance using the provider configured in the sidebar.
    """
    provider = None
    api_key = None
    session_model = None

    try:
        import streamlit as st
        if st.session_state.get("llm_configured"):
            provider = st.session_state.get("llm_provider")
            api_key = st.session_state.get("llm_api_key")
            session_model = st.session_state.get("llm_model")
    except Exception:
        pass

    if provider and api_key:
        return _create_llm_for_provider(
            provider, api_key, model or session_model, temperature
        )

    raise ValueError(
        "No LLM configured. Please select a provider and enter your API key "
        "in the sidebar (⚙️ LLM Configuration)."
    )


# ---------------------------------------------------------------------------
# Provider-specific constructors
# ---------------------------------------------------------------------------
def _create_llm_for_provider(provider, api_key, model, temperature):
    config = PROVIDER_MODELS.get(provider)
    if not config:
        raise ValueError(f"Unknown provider: {provider}")

    model = model or config["default_model"]
    class_name = config["class"]
    extra_kwargs = config.get("kwargs", {})

    if class_name == "ChatOpenAI":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model, temperature=temperature,
            api_key=api_key, **extra_kwargs,
        )

    if class_name == "ChatAnthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=model, temperature=temperature,
            api_key=api_key, **extra_kwargs,
        )

    if class_name == "ChatGoogleGenerativeAI":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=model, temperature=temperature,
            google_api_key=api_key, **extra_kwargs,
        )

    if class_name == "ChatGroq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=model, temperature=temperature,
            api_key=api_key, **extra_kwargs,
        )

    raise ValueError(f"Unsupported LLM class: {class_name}")



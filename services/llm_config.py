"""
Shared LLM configuration module.
Auto-detects API key format and configures the correct provider.
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


def get_llm(temperature: float = 0, model: str = "gpt-4o-mini") -> ChatOpenAI:
    """
    Create a ChatOpenAI instance with the correct provider configuration.

    Auto-detects whether the available key is for OpenRouter or OpenAI
    and configures base_url accordingly.

    Args:
        temperature: LLM temperature (default 0)
        model: Model name (default gpt-4o-mini)

    Returns:
        Configured ChatOpenAI instance
    """
    open_router_key = os.getenv("OPEN_ROUTER_KEY", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")

    # OpenRouter keys start with "sk-or-"
    if open_router_key and open_router_key.startswith("sk-or-"):
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=open_router_key,
            base_url="https://openrouter.ai/api/v1"
        )

    # OpenAI keys start with "sk-proj-" or "sk-"
    if open_router_key and open_router_key.startswith("sk-"):
        # Key is in OPEN_ROUTER_KEY but it's actually an OpenAI key
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=open_router_key,
        )

    if openai_key and openai_key.startswith("sk-"):
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=openai_key,
        )

    raise ValueError(
        "No valid API key found. Please set one of:\n"
        "  OPEN_ROUTER_KEY (OpenRouter key starting with sk-or-)\n"
        "  OPENAI_API_KEY (OpenAI key starting with sk-)\n"
        "in your .env file."
    )

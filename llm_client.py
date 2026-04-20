"""Factory for creating LLM clients (Gemini or Claude via Vertex AI)."""

import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_llm_client(provider: str = "auto"):
    """Create an LLM client based on the provider selection.

    Args:
        provider: "gemini", "claude", or "auto" (detect from env vars).

    Returns:
        An object with a `generate(prompt: str) -> str` method.
    """
    if provider == "auto":
        provider = _detect_provider()

    if provider == "claude":
        return _create_claude()
    elif provider == "gemini":
        return _create_gemini()
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


def _detect_provider() -> str:
    """Pick a provider based on which env vars are set."""
    llm_env = os.getenv("LLM_PROVIDER", "").lower()
    if llm_env in ("claude", "gemini"):
        return llm_env

    has_claude = bool(os.getenv("ANTHROPIC_VERTEX_PROJECT_ID"))
    has_gemini = bool(os.getenv("GEMINI_API_KEY"))

    if has_claude and not has_gemini:
        return "claude"
    if has_gemini and not has_claude:
        return "gemini"
    if has_claude and has_gemini:
        logger.info("Both Claude and Gemini configured; defaulting to Claude")
        return "claude"

    raise ValueError(
        "No LLM credentials found. Set GEMINI_API_KEY or "
        "ANTHROPIC_VERTEX_PROJECT_ID."
    )


def _create_claude():
    from claude_client import ClaudeClient
    logger.info("Using Claude via Vertex AI")
    return ClaudeClient()


def _create_gemini():
    from gemini_client import GeminiClient
    logger.info("Using Gemini")
    return GeminiClient()

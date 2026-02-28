"""
Provider pricing registry.
Per-token costs in USD. Update when providers change pricing.
All costs are per 1 token (not per 1K or 1M).
"""
from __future__ import annotations

# Format: "provider/model": {"input": cost_per_token, "output": cost_per_token}
PROVIDERS: dict[str, dict[str, float]] = {
    # Anthropic
    "anthropic/claude-haiku-4-5-20251001": {
        "input":  0.80 / 1_000_000,
        "output": 4.00 / 1_000_000,
    },
    "anthropic/claude-sonnet-4-6": {
        "input":  3.00 / 1_000_000,
        "output": 15.00 / 1_000_000,
    },
    "anthropic/claude-opus-4-6": {
        "input":  15.00 / 1_000_000,
        "output": 75.00 / 1_000_000,
    },
    # OpenAI
    "openai/gpt-4o": {
        "input":  2.50 / 1_000_000,
        "output": 10.00 / 1_000_000,
    },
    "openai/gpt-4o-mini": {
        "input":  0.15 / 1_000_000,
        "output": 0.60 / 1_000_000,
    },
    "openai/gpt-3.5-turbo": {
        "input":  0.50 / 1_000_000,
        "output": 1.50 / 1_000_000,
    },
    # Google
    "google/gemini-1.5-flash": {
        "input":  0.075 / 1_000_000,
        "output": 0.30 / 1_000_000,
    },
    "google/gemini-1.5-pro": {
        "input":  1.25 / 1_000_000,
        "output": 5.00 / 1_000_000,
    },
    # Local (always free)
    "ollama/qwen2.5:7b": {"input": 0.0, "output": 0.0},
    "ollama/llama3.2:3b": {"input": 0.0, "output": 0.0},
    "ollama/mistral:7b":  {"input": 0.0, "output": 0.0},
}


def compute_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """
    Calculate the USD cost of an LLM call.

    Args:
        model: Provider/model string e.g. "anthropic/claude-haiku-4-5-20251001"
        input_tokens: Number of input/prompt tokens
        output_tokens: Number of output/completion tokens

    Returns:
        Cost in USD (float). Returns 0.0 for unknown models (safe default).
    """
    pricing = PROVIDERS.get(model)
    if not pricing:
        # Unknown model — conservative: return 0 but emit a warning
        return 0.0
    return (input_tokens * pricing["input"]) + (output_tokens * pricing["output"])


def list_models() -> list[str]:
    """Return all registered model identifiers."""
    return sorted(PROVIDERS.keys())

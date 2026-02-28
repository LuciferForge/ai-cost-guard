# ai-cost-guard

[![PyPI version](https://img.shields.io/pypi/v/ai-cost-guard)](https://pypi.org/project/ai-cost-guard/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/ai-cost-guard)](https://pypi.org/project/ai-cost-guard/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)

**Budget enforcement and cost tracking for LLM applications.**

Stop runaway API spend from bugs, prompt injection, or retry loops — before it hits your credit card.

```python
from ai_cost_guard import CostGuard

guard = CostGuard(weekly_budget_usd=5.00)

@guard.protect(model="anthropic/claude-haiku-4-5-20251001")
def call_claude(prompt: str):
    return client.messages.create(...)   # blocked if budget exceeded
```

---

## Why this exists

When you build with LLMs, three things will eventually go wrong:

1. **A bug creates an infinite retry loop** — you wake up to a $300 bill.
2. **A prompt injection attack** causes your app to make thousands of unexpected calls.
3. **A junior dev accidentally calls GPT-4o** instead of GPT-4o-mini in a tight loop.

`ai-cost-guard` is a hard stop. It tracks every LLM call, accumulates cost,
and raises `BudgetExceededError` before the next call goes through.

Zero runtime dependencies. Pure Python stdlib. Works with any LLM provider.

---

## Install

```bash
pip install ai-cost-guard
```

Or from source:
```bash
git clone https://github.com/manja316/ai-cost-guard
cd ai-cost-guard
pip install -e ".[dev]"
```

---

## Quick Start

### Decorator (simplest)
```python
from ai_cost_guard import CostGuard
import anthropic

client = anthropic.Anthropic()
guard = CostGuard(weekly_budget_usd=5.00)

@guard.protect(model="anthropic/claude-haiku-4-5-20251001", purpose="summarizer")
def summarize(text: str):
    return client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        messages=[{"role": "user", "content": f"Summarize: {text}"}],
    )
```

### Manual check + record
```python
guard.check_budget("openai/gpt-4o", estimated_input=500, estimated_output=200)

response = openai_client.chat.completions.create(...)

guard.record(
    model="openai/gpt-4o",
    input_tokens=response.usage.prompt_tokens,
    output_tokens=response.usage.completion_tokens,
)
```

### Dry-run mode (test without real calls)
```python
guard = CostGuard(weekly_budget_usd=5.00, dry_run=True)
# All calls raise BudgetExceededError("DRY RUN") — safe to use in CI
```

---

## CLI

```bash
# Show current spend vs budget
ai-cost-guard status

# List all calls this period
ai-cost-guard calls

# List all registered models with pricing
ai-cost-guard models

# Check if a model call would be allowed given a budget
ai-cost-guard check anthropic/claude-sonnet-4-6 5.00

# Reset the tracker
ai-cost-guard reset
```

---

## Supported Providers

| Provider | Models |
|---|---|
| Anthropic | claude-haiku-4-5, claude-sonnet-4-6, claude-opus-4-6 |
| OpenAI | gpt-4o, gpt-4o-mini, gpt-3.5-turbo |
| Google | gemini-1.5-flash, gemini-1.5-pro |
| Ollama (local) | qwen2.5:7b, llama3.2:3b, mistral:7b (always $0.00) |

Adding a new model:
```python
from ai_cost_guard import PROVIDERS

PROVIDERS["myprovider/mymodel"] = {
    "input":  1.00 / 1_000_000,   # per token
    "output": 4.00 / 1_000_000,
}
```

---

## Security properties

- **Hard budget cap** — raises `BudgetExceededError` before the call, not after.
- **No network calls** — all data stored locally in `~/.ai-cost-guard/cost_log.json`.
- **Atomic writes** — cost log uses temp-file + rename to prevent corruption.
- **Zero dependencies** — nothing to supply-chain attack.
- **Audit trail** — every call logged with timestamp, model, tokens, and purpose.

See [SECURITY.md](SECURITY.md) for full security policy.

---

## How it compares

| Tool | Hard budget stop | Multi-provider | Zero deps | Local storage |
|---|---|---|---|---|
| **ai-cost-guard** | ✅ | ✅ | ✅ | ✅ |
| LangChain callbacks | ❌ (observe only) | ✅ | ❌ | ❌ |
| OpenAI usage limits | ✅ | ❌ | N/A | ❌ |
| Manual tracking | ❌ | depends | ✅ | depends |

---

## Running tests

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

---

## Contributing

PRs welcome. Please:
- Keep zero runtime dependencies.
- Add tests for new providers.
- Update pricing when providers change rates.

---

## License

MIT — free to use, modify, and distribute.

"""
ai-cost-guard — Budget enforcement and cost tracking for LLM applications.

Quick start:
    from ai_cost_guard import CostGuard, track_cost

    guard = CostGuard(weekly_budget_usd=5.00)

    @guard.protect
    def call_llm(prompt):
        # your LLM call here
        ...
"""
from .core.guard import CostGuard
from .core.tracker import CostTracker
from .core.providers import PROVIDERS

__version__ = "0.1.0"
__all__ = ["CostGuard", "CostTracker", "PROVIDERS"]

"""
CostGuard — budget enforcement layer for LLM calls.

Raises BudgetExceededError before an expensive call goes through.
Provides a @protect decorator for easy integration.

Security properties:
  - Hard budget cap prevents runaway spend from bugs or prompt injection
  - Dry-run mode lets you test without any API calls
  - All decisions are logged with timestamps for audit trails
"""
from __future__ import annotations

import functools
from typing import Callable, Optional

from .tracker import CostTracker
from .providers import compute_cost


class BudgetExceededError(Exception):
    """Raised when an LLM call would exceed the configured budget."""
    pass


class CostGuard:
    """
    Budget enforcer for LLM applications.

    Usage:
        guard = CostGuard(weekly_budget_usd=5.00)

        # As a context manager:
        with guard.check("anthropic/claude-haiku-4-5-20251001", est_input=500, est_output=200):
            response = client.messages.create(...)
            guard.record_actual(model, response.usage.input_tokens,
                                response.usage.output_tokens)

        # As a decorator:
        @guard.protect(model="anthropic/claude-haiku-4-5-20251001")
        def my_llm_call(prompt: str) -> str:
            ...
    """

    def __init__(
        self,
        weekly_budget_usd: float = 1.00,
        alert_at_pct: float = 0.80,       # Alert when 80% of budget used
        dry_run: bool = False,
        tracker: Optional[CostTracker] = None,
    ):
        self.budget = weekly_budget_usd
        self.alert_threshold = weekly_budget_usd * alert_at_pct
        self.dry_run = dry_run
        self.tracker = tracker or CostTracker()
        self._alert_sent = False

    # ── Core enforcement ──────────────────────────────────────────────────────

    def check_budget(
        self,
        model: str,
        estimated_input_tokens: int = 0,
        estimated_output_tokens: int = 0,
    ) -> None:
        """
        Check whether a call would exceed the budget.
        Raises BudgetExceededError if so.

        Call this BEFORE making an LLM API request.
        """
        current_spend = self.tracker.spent()
        estimated_cost = compute_cost(model, estimated_input_tokens, estimated_output_tokens)

        if current_spend >= self.budget:
            raise BudgetExceededError(
                f"Budget exhausted: spent ${current_spend:.4f} of ${self.budget:.2f} "
                f"this period. Call blocked."
            )

        if current_spend + estimated_cost > self.budget:
            raise BudgetExceededError(
                f"Call would exceed budget: current=${current_spend:.4f}, "
                f"estimated_cost=${estimated_cost:.4f}, budget=${self.budget:.2f}. "
                f"Call blocked."
            )

        # Near-budget alert (non-blocking)
        if not self._alert_sent and current_spend >= self.alert_threshold:
            self._emit_alert(current_spend)

    def record(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        purpose: str = "",
        backend: str = "api",
    ) -> float:
        """
        Record an actual completed LLM call. Returns the cost in USD.
        Call this AFTER a successful API response.
        """
        cost = compute_cost(model, input_tokens, output_tokens)
        if not self.dry_run:
            self.tracker.record(
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost,
                purpose=purpose,
                backend=backend,
            )
        return cost

    # ── Decorator ─────────────────────────────────────────────────────────────

    def protect(
        self,
        model: str,
        purpose: str = "",
        estimated_input: int = 1000,
        estimated_output: int = 500,
    ) -> Callable:
        """
        Decorator that wraps an LLM call with budget checking.

        The decorated function must return an object with a .usage attribute
        (compatible with Anthropic and OpenAI SDK responses).

        Example:
            @guard.protect(model="anthropic/claude-haiku-4-5-20251001")
            def call_claude(prompt: str):
                return client.messages.create(...)
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                self.check_budget(model, estimated_input, estimated_output)
                if self.dry_run:
                    raise BudgetExceededError("DRY RUN — no real API calls made.")
                result = func(*args, **kwargs)
                # Auto-record if response has usage info
                if hasattr(result, "usage"):
                    u = result.usage
                    in_tok  = getattr(u, "input_tokens",  getattr(u, "prompt_tokens",     0))
                    out_tok = getattr(u, "output_tokens", getattr(u, "completion_tokens",  0))
                    self.record(model, in_tok, out_tok, purpose=purpose)
                return result
            return wrapper
        return decorator

    # ── Status ────────────────────────────────────────────────────────────────

    def status(self) -> dict:
        """Return current budget status as a dict."""
        spent = self.tracker.spent()
        remaining = max(0.0, self.budget - spent)
        return {
            "budget_usd":    self.budget,
            "spent_usd":     round(spent, 6),
            "remaining_usd": round(remaining, 6),
            "pct_used":      round(spent / self.budget * 100, 1) if self.budget > 0 else 0,
            "dry_run":       self.dry_run,
            "detail":        self.tracker.summary(),
        }

    def is_safe(self) -> bool:
        """True if budget has not been exceeded."""
        return self.tracker.spent() < self.budget

    # ── Internal ─────────────────────────────────────────────────────────────

    def _emit_alert(self, current_spend: float) -> None:
        pct = int(current_spend / self.budget * 100)
        print(
            f"[ai-cost-guard] ⚠️  Budget alert: {pct}% used "
            f"(${current_spend:.4f} of ${self.budget:.2f})"
        )
        self._alert_sent = True

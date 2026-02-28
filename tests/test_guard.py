"""Tests for CostGuard budget enforcement."""
import tempfile
from pathlib import Path
import pytest

from ai_cost_guard.core.guard import CostGuard, BudgetExceededError
from ai_cost_guard.core.tracker import CostTracker


@pytest.fixture
def tmp_guard(tmp_path):
    tracker = CostTracker(log_path=tmp_path / "cost_log.json")
    return CostGuard(weekly_budget_usd=1.00, tracker=tracker)


def test_allows_call_within_budget(tmp_guard):
    # Should not raise
    tmp_guard.check_budget("anthropic/claude-haiku-4-5-20251001", 100, 50)


def test_blocks_call_when_budget_exhausted(tmp_path):
    tracker = CostTracker(log_path=tmp_path / "cost_log.json")
    tracker.record("anthropic/claude-sonnet-4-6", 1000, 500, cost_usd=1.50)
    guard = CostGuard(weekly_budget_usd=1.00, tracker=tracker)
    with pytest.raises(BudgetExceededError, match="Budget exhausted"):
        guard.check_budget("anthropic/claude-sonnet-4-6", 100, 50)


def test_blocks_call_that_would_exceed_budget(tmp_path):
    tracker = CostTracker(log_path=tmp_path / "cost_log.json")
    tracker.record("anthropic/claude-sonnet-4-6", 1000, 500, cost_usd=0.95)
    guard = CostGuard(weekly_budget_usd=1.00, tracker=tracker)
    # Large call that would push over $1.00
    with pytest.raises(BudgetExceededError, match="would exceed budget"):
        guard.check_budget("anthropic/claude-sonnet-4-6", 100_000, 50_000)


def test_dry_run_blocks_all_calls(tmp_path):
    tracker = CostTracker(log_path=tmp_path / "cost_log.json")
    guard = CostGuard(weekly_budget_usd=100.00, dry_run=True, tracker=tracker)

    @guard.protect(model="openai/gpt-4o")
    def fake_call():
        return "should not reach here"

    with pytest.raises(BudgetExceededError, match="DRY RUN"):
        fake_call()


def test_record_returns_cost(tmp_guard):
    cost = tmp_guard.record("anthropic/claude-haiku-4-5-20251001", 1000, 500)
    assert cost > 0.0


def test_status_structure(tmp_guard):
    status = tmp_guard.status()
    assert "budget_usd" in status
    assert "spent_usd" in status
    assert "remaining_usd" in status
    assert "pct_used" in status


def test_is_safe_when_under_budget(tmp_guard):
    assert tmp_guard.is_safe() is True


def test_is_unsafe_when_over_budget(tmp_path):
    tracker = CostTracker(log_path=tmp_path / "cost_log.json")
    tracker.record("openai/gpt-4o", 1000, 500, cost_usd=1.50)
    guard = CostGuard(weekly_budget_usd=1.00, tracker=tracker)
    assert guard.is_safe() is False


def test_zero_cost_local_models_always_allowed(tmp_path):
    tracker = CostTracker(log_path=tmp_path / "cost_log.json")
    tracker.record("ollama/qwen2.5:7b", 10000, 5000, cost_usd=0.0)
    guard = CostGuard(weekly_budget_usd=0.01, tracker=tracker)
    # Ollama is free — should never trigger budget guard
    guard.check_budget("ollama/qwen2.5:7b", 100_000, 50_000)

"""Tests for CostTracker."""
import json
import tempfile
from pathlib import Path
import pytest

from ai_cost_guard.core.tracker import CostTracker


@pytest.fixture
def tmp_tracker(tmp_path):
    return CostTracker(log_path=tmp_path / "cost_log.json")


def test_fresh_tracker_has_zero_spend(tmp_tracker):
    assert tmp_tracker.spent() == 0.0


def test_record_single_call(tmp_tracker):
    tmp_tracker.record("anthropic/claude-haiku-4-5-20251001", 100, 50, cost_usd=0.00025)
    assert tmp_tracker.spent() == pytest.approx(0.00025)


def test_record_multiple_calls_accumulate(tmp_tracker):
    tmp_tracker.record("openai/gpt-4o-mini", 200, 100, cost_usd=0.0001)
    tmp_tracker.record("openai/gpt-4o-mini", 300, 150, cost_usd=0.00015)
    assert tmp_tracker.spent() == pytest.approx(0.00025)


def test_calls_list(tmp_tracker):
    tmp_tracker.record("openai/gpt-4o", 100, 50, cost_usd=0.001, purpose="test")
    calls = tmp_tracker.calls()
    assert len(calls) == 1
    assert calls[0]["model"] == "openai/gpt-4o"
    assert calls[0]["purpose"] == "test"


def test_reset_clears_spend(tmp_tracker):
    tmp_tracker.record("anthropic/claude-sonnet-4-6", 500, 200, cost_usd=0.01)
    tmp_tracker.reset()
    assert tmp_tracker.spent() == 0.0
    assert len(tmp_tracker.calls()) == 0


def test_persistence_across_instances(tmp_path):
    log_path = tmp_path / "cost_log.json"
    t1 = CostTracker(log_path=log_path)
    t1.record("openai/gpt-4o-mini", 100, 50, cost_usd=0.0005)

    t2 = CostTracker(log_path=log_path)
    assert t2.spent() == pytest.approx(0.0005)


def test_summary_structure(tmp_tracker):
    tmp_tracker.record("anthropic/claude-haiku-4-5-20251001", 100, 50, cost_usd=0.0001, backend="api")
    tmp_tracker.record("ollama/qwen2.5:7b", 200, 100, cost_usd=0.0, backend="ollama")
    summary = tmp_tracker.summary()
    assert "spent_usd" in summary
    assert "by_model" in summary
    assert "by_backend" in summary
    assert summary["call_count"] == 2


def test_atomic_write_produces_valid_json(tmp_tracker):
    tmp_tracker.record("openai/gpt-4o", 100, 50, cost_usd=0.001)
    data = json.loads(tmp_tracker.log_path.read_text())
    assert "spent_usd" in data
    assert "calls" in data

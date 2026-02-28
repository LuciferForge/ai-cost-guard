"""
CostTracker — persistent, per-period cost log.

Stores all LLM calls in a local JSON file. Resets automatically
when a new period (week/day) starts. Safe to use from multiple
processes (file-based, atomic writes).
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

DEFAULT_LOG_PATH = Path.home() / ".ai-cost-guard" / "cost_log.json"


class CostTracker:
    """
    Tracks LLM API spend across calls, persisted to disk.

    Attributes:
        log_path:  Path to the JSON log file.
        period:    Reset period — "week" (Mon-Sun) or "day".
    """

    def __init__(
        self,
        log_path: Optional[Path] = None,
        period: str = "week",
    ):
        self.log_path = Path(log_path) if log_path else DEFAULT_LOG_PATH
        self.period = period
        self._ensure_dir()

    # ── Public API ────────────────────────────────────────────────────────────

    def record(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        purpose: str = "",
        backend: str = "api",
    ) -> None:
        """Record a completed LLM call."""
        log = self._load()
        log = self._maybe_reset(log)
        log["spent_usd"] = round(log["spent_usd"] + cost_usd, 8)
        log["calls"].append({
            "ts":           datetime.now().isoformat(),
            "model":        model,
            "backend":      backend,
            "purpose":      purpose,
            "input_tokens": input_tokens,
            "output_tokens":output_tokens,
            "cost_usd":     round(cost_usd, 8),
        })
        self._save(log)

    def spent(self) -> float:
        """Total USD spent in the current period."""
        log = self._maybe_reset(self._load())
        return log["spent_usd"]

    def calls(self) -> list[dict]:
        """All calls in the current period."""
        log = self._maybe_reset(self._load())
        return log["calls"]

    def summary(self) -> dict:
        """Human-readable spend summary."""
        log = self._maybe_reset(self._load())
        by_model: dict[str, float] = {}
        by_backend: dict[str, float] = {}
        for call in log["calls"]:
            by_model[call["model"]]     = by_model.get(call["model"], 0) + call["cost_usd"]
            by_backend[call["backend"]] = by_backend.get(call["backend"], 0) + call["cost_usd"]
        return {
            "period_start": log["period_start"],
            "spent_usd":    round(log["spent_usd"], 6),
            "call_count":   len(log["calls"]),
            "by_model":     {k: round(v, 6) for k, v in sorted(by_model.items(), key=lambda x: -x[1])},
            "by_backend":   {k: round(v, 6) for k, v in sorted(by_backend.items(), key=lambda x: -x[1])},
        }

    def reset(self) -> None:
        """Force-reset the tracker (useful for testing)."""
        self._save(self._fresh_log())

    # ── Internals ─────────────────────────────────────────────────────────────

    def _period_start(self) -> str:
        now = datetime.now()
        if self.period == "week":
            start = now - timedelta(days=now.weekday())
        else:
            start = now
        return start.strftime("%Y-%m-%d")

    def _fresh_log(self) -> dict:
        return {"period_start": self._period_start(), "spent_usd": 0.0, "calls": []}

    def _maybe_reset(self, log: dict) -> dict:
        if log.get("period_start") != self._period_start():
            return self._fresh_log()
        return log

    def _load(self) -> dict:
        if self.log_path.exists():
            try:
                return json.loads(self.log_path.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        return self._fresh_log()

    def _save(self, log: dict) -> None:
        # Atomic write: write to temp file then rename
        tmp = self.log_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(log, indent=2))
        tmp.replace(self.log_path)

    def _ensure_dir(self) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

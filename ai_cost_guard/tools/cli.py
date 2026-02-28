"""
CLI entry point: `ai-cost-guard` command.

Commands:
  ai-cost-guard status          — show current spend vs budget
  ai-cost-guard calls           — list all calls this period
  ai-cost-guard models          — list all registered models + pricing
  ai-cost-guard reset           — reset the tracker (with confirmation)
  ai-cost-guard check <model>   — check if a model call would be allowed
"""
from __future__ import annotations

import json
import sys

from ..core.tracker import CostTracker
from ..core.guard import CostGuard
from ..core.providers import list_models, PROVIDERS


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    cmd = args[0] if args else "status"

    tracker = CostTracker()

    if cmd == "status":
        summary = tracker.summary()
        print(f"\n{'─'*40}")
        print(f"  ai-cost-guard status")
        print(f"{'─'*40}")
        print(f"  Period start : {summary['period_start']}")
        print(f"  Total spent  : ${summary['spent_usd']:.6f}")
        print(f"  Call count   : {summary['call_count']}")
        if summary["by_model"]:
            print(f"\n  By model:")
            for model, cost in summary["by_model"].items():
                print(f"    {model:<45} ${cost:.6f}")
        if summary["by_backend"]:
            print(f"\n  By backend:")
            for backend, cost in summary["by_backend"].items():
                print(f"    {backend:<20} ${cost:.6f}")
        print(f"{'─'*40}\n")
        return 0

    elif cmd == "calls":
        calls = tracker.calls()
        if not calls:
            print("No calls recorded this period.")
            return 0
        print(f"\n{'─'*70}")
        print(f"  {'Timestamp':<25} {'Model':<35} {'Cost':>10}")
        print(f"{'─'*70}")
        for c in calls:
            ts = c["ts"][:19]
            model = c["model"][-35:]
            print(f"  {ts:<25} {model:<35} ${c['cost_usd']:>9.6f}")
        print(f"{'─'*70}\n")
        return 0

    elif cmd == "models":
        print(f"\n  Registered models ({len(PROVIDERS)}):")
        print(f"  {'Model':<50} {'Input/MTok':>12} {'Output/MTok':>12}")
        print(f"  {'─'*75}")
        for m in list_models():
            p = PROVIDERS[m]
            inp  = p["input"]  * 1_000_000
            out  = p["output"] * 1_000_000
            print(f"  {m:<50} ${inp:>10.3f}  ${out:>10.3f}")
        print()
        return 0

    elif cmd == "reset":
        confirm = input("Reset cost tracker? This clears all recorded calls. [y/N] ")
        if confirm.lower() == "y":
            tracker.reset()
            print("Tracker reset.")
        else:
            print("Cancelled.")
        return 0

    elif cmd == "check":
        if len(args) < 2:
            print("Usage: ai-cost-guard check <model> [budget_usd]")
            return 1
        model = args[1]
        budget = float(args[2]) if len(args) > 2 else 1.00
        guard = CostGuard(weekly_budget_usd=budget, tracker=tracker)
        try:
            guard.check_budget(model)
            print(f"✅  {model} call ALLOWED (spent ${guard.tracker.spent():.4f} of ${budget:.2f})")
        except Exception as e:
            print(f"🚫  {model} call BLOCKED: {e}")
        return 0

    else:
        print(f"Unknown command: {cmd}")
        print("Commands: status | calls | models | reset | check <model>")
        return 1


if __name__ == "__main__":
    sys.exit(main())

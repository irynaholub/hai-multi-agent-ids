"""Generate GPT reports for the intervals found by the orchestrator (needs an OpenAI API key)"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.dashboard_bundle import build_events, interval_label, load_detection_bundle
from src.llm_judge import LLMJudge


def main() -> None:
    parser = argparse.ArgumentParser(description="LLM anomaly reporter")
    parser.add_argument("--model", default="gpt-4o-mini")
    args = parser.parse_args()

    # Windows console may not be UTF-8, the reports are in Ukrainian
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    bundle = load_detection_bundle()
    if bundle.get("pred_cc") is None:
        raise SystemExit("Run apply_orchestrator_final.py first")

    events = build_events(bundle["pred_cc"], bundle["cr"], bundle["y_true"], bundle["target_mask"])
    tp_events = [e for e in events if e.extra.get("is_true_positive") == "True"]
    print(f"Detected intervals: {len(events)}, true positives on target attacks: {len(tp_events)}")

    judge = LLMJudge(model=args.model)

    for i, event in enumerate(tp_events, 1):
        print(f"\nInterval {i}/{len(tp_events)}: {interval_label(event)}")
        print(f"Active agents: {', '.join(event.active_agents) or 'none'}\n")

        report = judge.explain(event)
        print(report.text)
        print(f"\n[model={report.model}, tokens: {report.prompt_tokens}+{report.completion_tokens}]")


if __name__ == "__main__":
    main()

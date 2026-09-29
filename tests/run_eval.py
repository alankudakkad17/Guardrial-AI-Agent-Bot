"""Runs the labeled test cases against each guardrail and reports metrics.

Usage:
    python -m tests.run_eval

Requires GROQ_API_KEY to be set (see .env.example). Writes results to
tests/test_results.md.
"""

import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.guardrails import grounding_guard, injection_guard, scope_guard
from src.kb.snippets import SNIPPETS
from src.models import RetrievedSnippet
from tests.test_cases import GROUNDING_CASES, INJECTION_CASES, SCOPE_CASES
from tests.tool_output_injection_cases import TOOL_OUTPUT_INJECTION_CASES

_SNIPPETS_BY_ID = {s["id"]: s for s in SNIPPETS}


def _snippet_to_retrieved(snippet_id: str) -> RetrievedSnippet:
    s = _SNIPPETS_BY_ID[snippet_id]
    return RetrievedSnippet(id=s["id"], category=s["category"], title=s["title"], text=s["text"], distance=0.0)


def _eval_injection_cases(cases):
    rows = []
    latencies = []
    for case in cases:
        try:
            verdict, latency_ms = injection_guard.check(case["text"])
            latencies.append(latency_ms)
            predicted, error = verdict.is_injection, None
        except Exception as err:
            # A guard that can't produce a verdict at all is itself a
            # finding — report it as a miss rather than crashing the run.
            predicted, error = False, str(err)[:200]
        rows.append({**case, "predicted": predicted, "correct": predicted == case["label"], "error": error})

    tp_cases = [r for r in rows if r["type"] == "true_positive"]
    tn_cases = [r for r in rows if r["type"] == "true_negative"]
    adv_cases = [r for r in rows if r["type"] == "adversarial"]

    recall = sum(r["predicted"] for r in tp_cases) / len(tp_cases) if tp_cases else float("nan")
    fpr = sum(r["predicted"] for r in tn_cases) / len(tn_cases) if tn_cases else float("nan")
    adv_catch_rate = (
        sum(r["predicted"] == r["label"] for r in adv_cases) / len(adv_cases) if adv_cases else float("nan")
    )

    return {
        "rows": rows,
        "recall": recall,
        "false_positive_rate": fpr,
        "adversarial_accuracy": adv_catch_rate,
        "avg_latency_ms": (statistics.mean(latencies) if latencies else float("nan")),
    }


def eval_injection():
    return _eval_injection_cases(INJECTION_CASES)


def eval_tool_output_injection():
    """Same mechanism as eval_injection, run on tool-output-shaped text —
    tests injection_guard's reuse for indirect injection in src/agent.py."""
    return _eval_injection_cases(TOOL_OUTPUT_INJECTION_CASES)


def eval_scope():
    rows = []
    latencies = []
    for case in SCOPE_CASES:
        try:
            verdict, latency_ms = scope_guard.check(case["text"])
            latencies.append(latency_ms)
            predicted, error = verdict.category, None
        except Exception as err:
            predicted, error = "general_info", str(err)[:200]
        rows.append({**case, "predicted": predicted, "correct": predicted == case["label"], "error": error})

    blocking_cases = [r for r in rows if r["label"] != "general_info" and r["type"] != "adversarial"]
    negative_cases = [r for r in rows if r["label"] == "general_info" and r["type"] != "adversarial"]
    adv_cases = [r for r in rows if r["type"] == "adversarial"]

    recall = sum(r["correct"] for r in blocking_cases) / len(blocking_cases) if blocking_cases else float("nan")
    fpr = (
        sum(r["predicted"] != "general_info" for r in negative_cases) / len(negative_cases)
        if negative_cases
        else float("nan")
    )
    adv_accuracy = sum(r["correct"] for r in adv_cases) / len(adv_cases) if adv_cases else float("nan")

    return {
        "rows": rows,
        "recall": recall,
        "false_positive_rate": fpr,
        "adversarial_accuracy": adv_accuracy,
        "avg_latency_ms": (statistics.mean(latencies) if latencies else float("nan")),
    }


def eval_grounding():
    rows = []
    latencies = []
    for case in GROUNDING_CASES:
        snippets = [_snippet_to_retrieved(sid) for sid in case["snippet_ids"]]
        try:
            verdict, latency_ms = grounding_guard.check(case["draft_response"], snippets)
            latencies.append(latency_ms)
            predicted = verdict.claims[0].status if verdict.claims else "unsupported"
            error = None
        except Exception as err:
            predicted, error = "unsupported", str(err)[:200]
        rows.append({**case, "predicted": predicted, "correct": predicted == case["label"], "error": error})

    by_type = {}
    for label in ("grounded", "ungrounded_but_plausible", "unsupported"):
        subset = [r for r in rows if r["label"] == label]
        by_type[label] = sum(r["correct"] for r in subset) / len(subset) if subset else float("nan")

    overall_accuracy = sum(r["correct"] for r in rows) / len(rows) if rows else float("nan")

    return {
        "rows": rows,
        "accuracy_by_label": by_type,
        "overall_accuracy": overall_accuracy,
        "avg_latency_ms": (statistics.mean(latencies) if latencies else float("nan")),
    }


def _fmt_pct(x: float) -> str:
    return "n/a" if x != x else f"{x * 100:.1f}%"


def _fmt_correct(r: dict) -> str:
    if r.get("error"):
        return f"⚠️ error: {r['error'][:80]}"
    return "✓" if r["correct"] else "✗"


def write_report(injection_results, tool_injection_results, scope_results, grounding_results, path: Path):
    lines = ["# Test Results\n"]

    lines.append("## Injection / Jailbreak Guardrail (user input)\n")
    lines.append(f"- Recall on true positives: {_fmt_pct(injection_results['recall'])}")
    lines.append(f"- False positive rate on true negatives: {_fmt_pct(injection_results['false_positive_rate'])}")
    lines.append(f"- Adversarial case accuracy: {_fmt_pct(injection_results['adversarial_accuracy'])}")
    lines.append(f"- Avg latency: {injection_results['avg_latency_ms']:.0f} ms\n")
    lines.append("| Input | Type | Expected | Predicted | Correct |")
    lines.append("|---|---|---|---|---|")
    for r in injection_results["rows"]:
        lines.append(f"| {r['text'][:60]} | {r['type']} | {r['label']} | {r['predicted']} | {_fmt_correct(r)} |")

    lines.append("\n## Indirect Injection Guardrail (tool output — agent-specific)\n")
    lines.append(f"- Recall on true positives: {_fmt_pct(tool_injection_results['recall'])}")
    lines.append(f"- False positive rate on true negatives: {_fmt_pct(tool_injection_results['false_positive_rate'])}")
    lines.append(f"- Adversarial case accuracy: {_fmt_pct(tool_injection_results['adversarial_accuracy'])}")
    lines.append(f"- Avg latency: {tool_injection_results['avg_latency_ms']:.0f} ms\n")
    lines.append("| Tool output | Type | Expected | Predicted | Correct |")
    lines.append("|---|---|---|---|---|")
    for r in tool_injection_results["rows"]:
        lines.append(f"| {r['text'][:60]} | {r['type']} | {r['label']} | {r['predicted']} | {_fmt_correct(r)} |")

    lines.append("\n## Scope-of-Practice Guardrail\n")
    lines.append(f"- Recall on true positives: {_fmt_pct(scope_results['recall'])}")
    lines.append(f"- False positive rate on true negatives: {_fmt_pct(scope_results['false_positive_rate'])}")
    lines.append(f"- Adversarial case accuracy: {_fmt_pct(scope_results['adversarial_accuracy'])}")
    lines.append(f"- Avg latency: {scope_results['avg_latency_ms']:.0f} ms\n")
    lines.append("| Input | Type | Expected | Predicted | Correct |")
    lines.append("|---|---|---|---|---|")
    for r in scope_results["rows"]:
        lines.append(f"| {r['text'][:60]} | {r['type']} | {r['label']} | {r['predicted']} | {_fmt_correct(r)} |")

    lines.append("\n## Grounding Guardrail\n")
    for label, acc in grounding_results["accuracy_by_label"].items():
        lines.append(f"- Accuracy on `{label}`: {_fmt_pct(acc)}")
    lines.append(f"- Overall accuracy: {_fmt_pct(grounding_results['overall_accuracy'])}")
    lines.append(f"- Avg latency: {grounding_results['avg_latency_ms']:.0f} ms\n")
    lines.append("| Claim | Expected | Predicted | Correct |")
    lines.append("|---|---|---|---|")
    for r in grounding_results["rows"]:
        lines.append(f"| {r['draft_response'][:60]} | {r['label']} | {r['predicted']} | {_fmt_correct(r)} |")

    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    print("Evaluating injection guardrail (user input)...")
    injection_results = eval_injection()
    print("Evaluating indirect injection guardrail (tool output)...")
    tool_injection_results = eval_tool_output_injection()
    print("Evaluating scope guardrail...")
    scope_results = eval_scope()
    print("Evaluating grounding guardrail...")
    grounding_results = eval_grounding()

    out_path = Path(__file__).parent / "test_results.md"
    write_report(injection_results, tool_injection_results, scope_results, grounding_results, out_path)
    print(f"Results written to {out_path}")

"""Tool registry for the agent: schemas, risk levels, and implementations.

Risk level is a static attribute per tool, not a judged classification:
read_only tools execute immediately, the one action tool always pauses for
explicit user confirmation before it runs (see src/agent.py).
"""

from src import retrieval
from src.models import RetrievedSnippet

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_kb",
            "description": (
                "Search the general medical knowledge base for information "
                "relevant to a query. Use this for follow-up lookups when "
                "the snippets already provided aren't enough to answer."
            ),
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_drug_interaction",
            "description": "Check whether there is a known interaction between two medications.",
            "parameters": {
                "type": "object",
                "properties": {
                    "drug_a": {"type": "string"},
                    "drug_b": {"type": "string"},
                },
                "required": ["drug_a", "drug_b"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "triage_lookup",
            "description": (
                "Check whether a described set of symptoms matches a known "
                "emergency triage red flag."
            ),
            "parameters": {
                "type": "object",
                "properties": {"symptoms": {"type": "string"}},
                "required": ["symptoms"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "request_pharmacist_review",
            "description": (
                "Escalate the user's question to a pharmacist for review. "
                "This is a real-world action, not an information lookup — "
                "only call it if the user explicitly wants that escalation. "
                "It always pauses for the user's explicit confirmation "
                "before actually being sent."
            ),
            "parameters": {
                "type": "object",
                "properties": {"note": {"type": "string"}},
                "required": ["note"],
            },
        },
    },
]

TOOL_RISK = {
    "search_kb": "read_only",
    "check_drug_interaction": "read_only",
    "triage_lookup": "read_only",
    "request_pharmacist_review": "action",
}


def _format_snippets(snippets: list[RetrievedSnippet]) -> str:
    return "\n\n".join(f"[{s.id}] {s.title}\n{s.text}" for s in snippets)


def _search_kb(args: dict) -> tuple[str, list[RetrievedSnippet]]:
    snippets = retrieval.search(args["query"], k=3)
    if not snippets:
        return "No relevant information found in the knowledge base.", []
    return _format_snippets(snippets), snippets


def _check_drug_interaction(args: dict) -> tuple[str, list[RetrievedSnippet]]:
    drug_a, drug_b = args["drug_a"], args["drug_b"]
    snippets = retrieval.search(f"interaction between {drug_a} and {drug_b}", k=2, category="interaction")
    if not snippets:
        return f"No known interaction found in the knowledge base between {drug_a} and {drug_b}.", []
    return _format_snippets(snippets), snippets


def _triage_lookup(args: dict) -> tuple[str, list[RetrievedSnippet]]:
    snippets = retrieval.search(args["symptoms"], k=2, category="triage")
    if not snippets:
        return "No matching emergency red-flag pattern found for these symptoms.", []
    return _format_snippets(snippets), snippets


def _request_pharmacist_review(args: dict) -> tuple[str, list[RetrievedSnippet]]:
    note = args["note"]
    return (
        f"[SIMULATED] Pharmacist review requested with note: {note!r}. "
        "(No real message was sent — this is a mocked action tool.)",
        [],
    )


_IMPLEMENTATIONS = {
    "search_kb": _search_kb,
    "check_drug_interaction": _check_drug_interaction,
    "triage_lookup": _triage_lookup,
    "request_pharmacist_review": _request_pharmacist_review,
}


def execute_tool(tool_name: str, arguments: dict) -> tuple[str, list[RetrievedSnippet]]:
    """Returns (observation_text, snippets_used)."""
    return _IMPLEMENTATIONS[tool_name](arguments)

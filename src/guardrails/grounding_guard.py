"""Output guardrail: grounding/citation check.

Breaks the generated response into claims and classifies each against the
retrieved snippets as grounded / ungrounded-but-plausible / unsupported,
then produces a revised response that suppresses unsupported claims and
hedges ungrounded ones.
"""

import time

from src.llm_client import JUDGE_MODEL, call_json
from src.models import GroundingVerdict, RetrievedSnippet

_SYSTEM_PROMPT = """You are a grounding auditor for a medical information \
assistant that must only make claims supported by retrieved reference \
snippets. You will be given the retrieved snippets and the assistant's \
draft response.

Break the draft response into individual factual claims and classify each:
- "grounded": directly supported by one or more of the retrieved snippets.
- "ungrounded_but_plausible": a reasonable general-knowledge statement, but \
not found in the retrieved snippets (should be hedged, not deleted).
- "unsupported": not supported by the snippets and not reliable \
general knowledge (should be removed).

Then produce a "revised_response": the draft rewritten so that unsupported \
claims are removed, ungrounded-but-plausible claims are hedged (e.g. "this \
isn't in my reference material, but generally...") and grounded claims are \
left intact. Keep the tone natural and keep the response helpful.

Respond with JSON matching this schema:
{"claims": [{"claim": str, "status": one of the three strings above, \
"supporting_snippet_ids": [str]}], "revised_response": str}"""


def _format_snippets(snippets: list[RetrievedSnippet]) -> str:
    return "\n\n".join(f"[{s.id}] {s.title}\n{s.text}" for s in snippets)


def check(draft_response: str, snippets: list[RetrievedSnippet]) -> tuple[GroundingVerdict, float]:
    """Returns (verdict, latency_ms)."""
    user_content = (
        f"RETRIEVED SNIPPETS:\n{_format_snippets(snippets)}\n\n"
        f"DRAFT RESPONSE:\n{draft_response}"
    )
    return call_json(
        system=_SYSTEM_PROMPT,
        user=user_content,
        response_model=GroundingVerdict,
        model=JUDGE_MODEL,
    )

# Example Runs

Placeholder — fill in with 5-8 annotated before/after examples once the
assistant has been run interactively (`python main.py`) or via the eval
harness. For each example, capture:

- Input
- Response without guardrails (raw generation)
- Response with guardrails
- Verdict / what the guardrail caught

Example template:

## Example 1: Dosage request

- **Input:** "How much ibuprofen should I take for my 80lb dog?"
- **Without guardrails:** *(raw LLM response, likely gives a number)*
- **With guardrails:** *(scope_guard fallback response)*
- **Verdict:** `dosage_request` — short-circuited before retrieval/generation.

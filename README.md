# Guardrailed Medical Information Agent

A small tool-using agent for general medical/health information, wrapped
in guardrails on three layers: input (prompt-injection detection,
scope-of-practice enforcement), tool-use (an action-tool confirmation
gate, indirect-injection scanning of tool output, an iteration budget
cap), and output (grounding verification).

See [DESIGN.md](DESIGN.md) for the full design rationale and
[docs/evaluation.md](docs/evaluation.md) for the write-up of what worked and
what didn't.

## Setup

Use a virtual environment — this avoids picking up broken/conflicting
packages from a shared global Python install.

```bash
python -m venv .venv
.venv\Scripts\activate       # Windows
pip install -r requirements.txt
cp .env.example .env  # then fill in GROQ_API_KEY and the CHROMA_* values
```

Get a Groq API key at https://console.groq.com/keys and a Chroma Cloud
API key/tenant/database at https://trychroma.com.

## Run the agent

```bash
python main.py
```

The CLI prints a step-by-step trace after each response — which tools were
called, whether any tool output was flagged as suspicious, and (for the
action tool) an explicit confirmation prompt before it actually executes.

## Run the web frontend

```bash
python app.py
```

Opens a Gradio chat UI at http://localhost:7860 with the same guardrail
trace shown alongside the conversation (initial retrieval, tool calls,
flagged/suspicious tool output, claim grounding statuses, and the
confirmation prompt for the action tool — reply "yes" in the chat to
confirm it, anything else to cancel).

## Run the guardrail evaluation

```bash
python -m tests.run_eval
```

Runs the labeled cases in [tests/test_cases.py](tests/test_cases.py) and
[tests/tool_output_injection_cases.py](tests/tool_output_injection_cases.py)
against the LLM-judged guardrails, writing metrics + before/after tables to
`tests/test_results.md`.

```bash
python -m tests.test_agent_structural
```

Runs plain, mocked assertions (no network calls, no LLM judgment) proving
the two *structural* guardrails hold: the action tool never executes
without going through confirmation, and the loop always terminates at
`MAX_ITERATIONS` instead of hanging.

## Architecture

```
User message
   |
   v
[Input Guardrails]
   |-- Injection/jailbreak detector (regex pre-filter + Groq LLM judge)
   `-- Scope-of-practice classifier (diagnosis / dosage / prescription / emergency)
   |   (if flagged -> safe templated response; pipeline short-circuits here)
   v
[Seeded Retrieval]
   `-- all-MiniLM-L6-v2 embeddings (via Chroma's ONNX runtime embedder) in a
       Chroma Cloud vector DB (~18 snippets), searched once automatically
       so grounding always has something to check against
   v
[Agent Loop]  (Groq openai/gpt-oss-120b, native tool-calling, up to 5 steps)
   |-- model decides: answer directly, or call a tool
   |-- read_only tools (search_kb, check_drug_interaction, triage_lookup):
   |     execute -> scan result with injection_guard (indirect-injection
   |     check on tool output) -> feed back real result, or a sanitized
   |     notice if flagged -> loop
   |-- action tool (request_pharmacist_review):
   |     ALWAYS stops the loop and returns a confirmation request instead
   |     of executing — never judged, always required
   `-- hits MAX_ITERATIONS without a final answer -> stop, fallback message
   v
[Output Guardrail]
   `-- Grounding check over ALL snippets gathered across the whole
       trajectory: classify each claim grounded / ungrounded-but-plausible
       / unsupported, then hedge/suppress
   v
Response to user (+ step-by-step trace)
```

## Project layout

```
src/
  guardrails/
    injection_guard.py   # input + tool-output: prompt injection / jailbreak detection
    scope_guard.py        # input: scope-of-practice classification
    grounding_guard.py    # output: claim grounding check
  kb/snippets.py          # curated knowledge base (~18 snippets)
  retrieval.py            # Chroma Cloud-backed embedding search (optional category filter)
  tools.py                # tool schemas, risk levels (read_only/action), implementations
  llm_client.py            # Groq API wrapper (text, JSON-mode, and tool-calling)
  models.py               # Pydantic models for verdicts/traces
  agent.py                # orchestrates: guardrails -> seeded retrieval -> tool loop -> grounding
tests/
  test_cases.py                    # labeled examples for the 3 original guardrails
  tool_output_injection_cases.py   # labeled examples for indirect injection via tool output
  run_eval.py                      # computes recall/FPR/latency, writes test_results.md
main.py                            # CLI frontend
app.py                             # Gradio web frontend (same agent, trace shown alongside chat)
  test_agent_structural.py         # mocked, code-level checks for confirmation gate + iteration cap
```

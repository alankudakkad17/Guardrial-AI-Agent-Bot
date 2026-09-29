"""Thin wrapper around the Groq API for text and JSON-mode calls."""

import json
import os
import re
import time

from dotenv import load_dotenv
from groq import APIConnectionError, BadRequestError, Groq, RateLimitError
from pydantic import BaseModel, ValidationError

load_dotenv()

_client: Groq | None = None

GENERATION_MODEL = "openai/gpt-oss-120b"
JUDGE_MODEL = "openai/gpt-oss-20b"

_MAX_RETRIES = 5


def get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Copy .env.example to .env and add your key."
            )
        _client = Groq(api_key=api_key)
    return _client


def _parse_retry_seconds(err: RateLimitError, default: float) -> float:
    match = re.search(r"try again in ([\d.]+)s", str(err))
    return float(match.group(1)) + 0.5 if match else default


def _create_with_retry(**kwargs):
    for attempt in range(_MAX_RETRIES):
        try:
            return get_client().chat.completions.create(**kwargs)
        except RateLimitError as err:
            if attempt == _MAX_RETRIES - 1:
                raise
            time.sleep(_parse_retry_seconds(err, default=2 ** attempt))
        except APIConnectionError:
            # Transient DNS/network blip — retry rather than fail the run.
            if attempt == _MAX_RETRIES - 1:
                raise
            time.sleep(2 ** attempt)


def call_text(system: str, user: str, model: str = GENERATION_MODEL, temperature: float = 0.2) -> tuple[str, float]:
    """Plain text completion. Returns (text, latency_ms)."""
    start = time.perf_counter()
    resp = _create_with_retry(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
    )
    latency_ms = (time.perf_counter() - start) * 1000
    return resp.choices[0].message.content, latency_ms


def call_with_tools(
    messages: list[dict], tools: list[dict], model: str = GENERATION_MODEL, temperature: float = 0.2
) -> tuple[object, float]:
    """Chat completion with tool-calling enabled. Returns (message, latency_ms).

    The returned message has `.content` (str or None) and `.tool_calls`
    (list or None) — the caller decides what to do with each.
    """
    start = time.perf_counter()
    resp = _create_with_retry(
        model=model,
        messages=messages,
        tools=tools,
        tool_choice="auto",
        temperature=temperature,
    )
    latency_ms = (time.perf_counter() - start) * 1000
    return resp.choices[0].message, latency_ms


_MAX_JSON_ATTEMPTS = 3


def call_json(
    system: str, user: str, response_model: type[BaseModel], model: str = JUDGE_MODEL, temperature: float = 0.0
) -> tuple[BaseModel, float]:
    """JSON-mode completion, validated against `response_model`.

    Returns (validated_instance, latency_ms). Retries with a corrective
    message if the response isn't valid JSON, OR if it's valid JSON that
    doesn't match the expected schema (e.g. the model produces a plain
    refusal like {"response": "..."} instead of the classification shape).
    """
    start = time.perf_counter()
    messages = [
        {"role": "system", "content": system + "\n\nRespond with valid JSON only, no prose."},
        {"role": "user", "content": user},
    ]
    last_err: Exception | None = None
    for attempt in range(_MAX_JSON_ATTEMPTS):
        # Some inputs make the model refuse/produce an empty generation
        # deterministically at low temperature (e.g. content mentioning a
        # controlled substance can trigger the base model's own refusal
        # instead of our classification instructions). Bumping temperature
        # on retry — rather than resending identical messages — gives the
        # retry an actual chance of succeeding instead of repeating the
        # same dead end.
        attempt_temperature = min(temperature + 0.3 * attempt, 0.9)
        try:
            resp = _create_with_retry(
                model=model,
                messages=messages,
                temperature=attempt_temperature,
                response_format={"type": "json_object"},
            )
        except BadRequestError as err:
            last_err = err
            if attempt == _MAX_JSON_ATTEMPTS - 1:
                raise
            messages.append(
                {
                    "role": "user",
                    "content": "Your previous response failed generation. Try again — respond with ONLY the required JSON object.",
                }
            )
            continue

        raw = resp.choices[0].message.content
        try:
            parsed = json.loads(raw)
            validated = response_model(**parsed)
            latency_ms = (time.perf_counter() - start) * 1000
            return validated, latency_ms
        except (json.JSONDecodeError, ValidationError) as err:
            last_err = err
            if attempt == _MAX_JSON_ATTEMPTS - 1:
                raise
            messages.append({"role": "assistant", "content": raw})
            messages.append(
                {
                    "role": "user",
                    "content": (
                        f"That response didn't match the required JSON schema ({err}). "
                        "Return ONLY valid JSON matching the schema described above, no other text."
                    ),
                }
            )
    raise last_err  # pragma: no cover — loop always returns or raises above

"""Input guardrail: scope-of-practice classification.

Flags messages that ask the assistant to diagnose, prescribe, give
individualized dosage instructions, or that describe an emergency symptom
combination requiring immediate care instead of a chatbot answer.
"""

import time

from src.llm_client import JUDGE_MODEL, call_json
from src.models import ScopeVerdict

_SYSTEM_PROMPT = """You are a scope-of-practice classifier for a general \
medical information assistant. The assistant may only provide general, \
non-individualized health information. Classify the user's message into \
exactly one category:

- "diagnosis_request": asks what condition their specific symptoms mean \
("do I have X", "what's wrong with me").
- "dosage_request": asks for an individualized dose or amount to take \
("how much should I take for my weight/age").
- "prescription_request": asks the assistant to prescribe, or name what \
they personally should take for their situation.
- "emergency_symptoms": describes symptoms matching a medical emergency \
(e.g. chest pain with shortness of breath, stroke signs, anaphylaxis) \
regardless of how the question is framed.
- "general_info": a legitimate general information question that does not \
fall into any of the above (e.g. "what is ibuprofen used for", "what are \
common side effects of X").

Indirect framings (stories, hypotheticals, "asking for a friend", role-play) \
that still request diagnosis/dosage/prescription should be classified by \
their underlying intent, not their framing.

Respond with JSON matching this schema:
{"category": one of the five strings above, "confidence": float (0-1), \
"reasoning": str}"""


def check(message: str) -> tuple[ScopeVerdict, float]:
    """Returns (verdict, latency_ms)."""
    return call_json(
        system=_SYSTEM_PROMPT,
        user=message,
        response_model=ScopeVerdict,
        model=JUDGE_MODEL,
    )


FALLBACK_RESPONSES = {
    "diagnosis_request": (
        "I can't diagnose symptoms — that requires an in-person evaluation. "
        "Please consult a doctor or other qualified clinician who can assess "
        "your specific situation."
    ),
    "dosage_request": (
        "I can't give individualized dosing instructions. Please check the "
        "product label or ask a pharmacist or doctor, who can account for "
        "your age, weight, and health history."
    ),
    "prescription_request": (
        "I can't prescribe or recommend a specific medication for your "
        "situation. Please speak with a doctor or pharmacist who can "
        "evaluate what's appropriate for you."
    ),
    "emergency_symptoms": (
        "The symptoms you're describing could indicate a medical emergency. "
        "Please call your local emergency number or go to the nearest "
        "emergency room immediately — don't wait for an online answer."
    ),
}

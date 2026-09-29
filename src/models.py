"""Shared Pydantic models for guardrail verdicts and retrieval results."""

from typing import Literal
from pydantic import BaseModel, Field


class InjectionVerdict(BaseModel):
    is_injection: bool = Field(
        description="True if the message attempts to override system "
        "instructions, jailbreak the assistant, or extract prohibited "
        "behavior via indirection (e.g. role-play, hypotheticals, translation)."
    )
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = Field(description="Brief justification for the verdict.")


ScopeCategory = Literal[
    "diagnosis_request",
    "dosage_request",
    "prescription_request",
    "emergency_symptoms",
    "general_info",
]


class ScopeVerdict(BaseModel):
    category: ScopeCategory
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = Field(description="Brief justification for the category.")

    @property
    def is_blocked(self) -> bool:
        return self.category != "general_info"


class RetrievedSnippet(BaseModel):
    id: str
    category: str
    title: str
    text: str
    distance: float


ClaimStatus = Literal["grounded", "ungrounded_but_plausible", "unsupported"]


class ClaimVerdict(BaseModel):
    claim: str
    status: ClaimStatus
    supporting_snippet_ids: list[str] = Field(default_factory=list)


class GroundingVerdict(BaseModel):
    claims: list[ClaimVerdict]
    revised_response: str = Field(
        description="The response rewritten to suppress unsupported claims and "
        "add hedging language to ungrounded-but-plausible claims. Grounded "
        "claims are left as-is."
    )

    @property
    def has_unsupported(self) -> bool:
        return any(c.status == "unsupported" for c in self.claims)

    @property
    def has_ungrounded(self) -> bool:
        return any(c.status == "ungrounded_but_plausible" for c in self.claims)


class GuardrailTrace(BaseModel):
    injection: InjectionVerdict | None = None
    scope: ScopeVerdict | None = None
    grounding: GroundingVerdict | None = None
    retrieved_ids: list[str] = Field(default_factory=list)
    short_circuited_at: str | None = None
    latency_ms: dict[str, float] = Field(default_factory=dict)


class ChatResult(BaseModel):
    response: str
    trace: GuardrailTrace


ToolRisk = Literal["read_only", "action"]


class ToolCallRecord(BaseModel):
    tool_name: str
    arguments: dict
    risk: ToolRisk
    observation: str
    flagged_as_suspicious: bool = False


class PendingAction(BaseModel):
    tool_name: str
    arguments: dict
    note_to_user: str


class AgentTrace(BaseModel):
    injection: InjectionVerdict | None = None
    scope: ScopeVerdict | None = None
    grounding: GroundingVerdict | None = None
    retrieved_ids: list[str] = Field(default_factory=list)
    steps: list[ToolCallRecord] = Field(default_factory=list)
    short_circuited_at: str | None = None
    stopped_at_max_iterations: bool = False
    pending_action: PendingAction | None = None
    latency_ms: dict[str, float] = Field(default_factory=dict)


class AgentResult(BaseModel):
    response: str
    trace: AgentTrace

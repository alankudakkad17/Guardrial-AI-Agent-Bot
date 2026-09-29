"""Structural guarantees for the agent loop — plain assertions, not LLM-judged
eval. These mock the LLM/guardrail calls so they run deterministically
without hitting the network.

Run: python -m tests.test_agent_structural
"""

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import agent
from src.models import InjectionVerdict, ScopeVerdict

_NO_INJECTION = (InjectionVerdict(is_injection=False, confidence=0.0, reasoning="n/a"), 0.0)
_GENERAL_INFO = (ScopeVerdict(category="general_info", confidence=1.0, reasoning="n/a"), 0.0)


def _fake_tool_call(call_id, name, arguments_json):
    function = SimpleNamespace(name=name, arguments=arguments_json)
    return SimpleNamespace(id=call_id, type="function", function=function)


def test_action_tool_never_executes_without_confirmation():
    """The action tool must never run inside the loop — only via execute_pending_action."""
    action_message = SimpleNamespace(
        content=None,
        tool_calls=[_fake_tool_call("call_1", "request_pharmacist_review", '{"note": "test note"}')],
    )

    executed = []
    real_execute = agent.tools.execute_tool

    def spy_execute_tool(tool_name, args):
        executed.append(tool_name)
        return real_execute(tool_name, args)

    with patch("src.agent.injection_guard.check", return_value=_NO_INJECTION), \
         patch("src.agent.scope_guard.check", return_value=_GENERAL_INFO), \
         patch("src.agent.retrieval.search", return_value=[]), \
         patch("src.agent.call_with_tools", return_value=(action_message, 0.0)), \
         patch("src.agent.tools.execute_tool", side_effect=spy_execute_tool):
        result = agent.answer("please escalate this to a pharmacist")

    assert executed == [], f"action tool executed inside the loop without confirmation: {executed}"
    assert result.trace.pending_action is not None
    assert result.trace.pending_action.tool_name == "request_pharmacist_review"

    # The only path that should actually execute it: explicit confirmation.
    observation = agent.execute_pending_action(result.trace.pending_action)
    assert "SIMULATED" in observation
    print("PASS: action tool only executes via explicit confirmation")


def test_loop_terminates_at_max_iterations():
    """If the model always requests a read-only tool, the loop must stop, not hang forever."""
    forever_message = SimpleNamespace(
        content=None,
        tool_calls=[_fake_tool_call("call_x", "search_kb", '{"query": "anything"}')],
    )
    call_count = {"n": 0}

    def fake_call_with_tools(messages, tool_schemas, model=None, temperature=0.2):
        call_count["n"] += 1
        return forever_message, 0.0

    with patch("src.agent.injection_guard.check", return_value=_NO_INJECTION), \
         patch("src.agent.scope_guard.check", return_value=_GENERAL_INFO), \
         patch("src.agent.retrieval.search", return_value=[]), \
         patch("src.agent.call_with_tools", side_effect=fake_call_with_tools), \
         patch("src.agent.tools.execute_tool", return_value=("no information found", [])):
        result = agent.answer("keep looking forever")

    assert call_count["n"] == agent.MAX_ITERATIONS, (
        f"expected exactly {agent.MAX_ITERATIONS} model calls, got {call_count['n']}"
    )
    assert result.trace.stopped_at_max_iterations is True
    assert result.response == agent.MAX_ITERATIONS_FALLBACK
    print(f"PASS: loop terminates at MAX_ITERATIONS={agent.MAX_ITERATIONS} instead of hanging")


if __name__ == "__main__":
    test_action_tool_never_executes_without_confirmation()
    test_loop_terminates_at_max_iterations()
    print("\nAll structural guarantees hold.")

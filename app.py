"""Gradio web frontend for the guardrailed medical information agent."""

import gradio as gr

from src import agent
from src.models import AgentTrace, PendingAction

DISCLAIMER = (
    "General health information only — not a substitute for professional "
    "medical advice. If this is a real emergency, call emergency services."
)


def _format_trace(trace: AgentTrace) -> str:
    lines = []
    if trace.short_circuited_at:
        lines.append(f"**Short-circuited at:** `{trace.short_circuited_at}`")
        if trace.injection:
            lines.append(
                f"- injection: `{trace.injection.is_injection}` "
                f"(confidence {trace.injection.confidence:.2f})"
            )
        if trace.scope:
            lines.append(
                f"- scope: `{trace.scope.category}` "
                f"(confidence {trace.scope.confidence:.2f})"
            )
    elif trace.pending_action:
        lines.append(f"**Awaiting confirmation for:** `{trace.pending_action.tool_name}`")
        lines.append(f"- arguments: `{trace.pending_action.arguments}`")
        lines.append("- reply **yes** to confirm, anything else to cancel")
    else:
        lines.append(f"**Initial retrieval:** `{trace.retrieved_ids}`")
        for step in trace.steps:
            flag = " ⚠️ **FLAGGED AS SUSPICIOUS**" if step.flagged_as_suspicious else ""
            lines.append(f"- tool call: `{step.tool_name}({step.arguments})`{flag}")
        if trace.stopped_at_max_iterations:
            lines.append("- stopped: max iterations reached")
        if trace.grounding:
            statuses = [c.status for c in trace.grounding.claims]
            lines.append(f"- claim statuses: `{statuses}`")

    total_latency = sum(trace.latency_ms.values())
    lines.append(f"\n**Total added latency:** {total_latency:.0f} ms")
    return "\n".join(lines)


def respond(user_message: str, history: list, pending_action: PendingAction | None):
    if not user_message.strip():
        return history, pending_action, gr.update()

    history = history + [{"role": "user", "content": user_message}]

    if pending_action is not None:
        if user_message.strip().lower() in {"yes", "y", "confirm"}:
            observation = agent.execute_pending_action(pending_action)
            response = observation
        else:
            response = "Okay, cancelled that action."
        history = history + [{"role": "assistant", "content": response}]
        return history, None, "_Action resolved — awaiting your next message._"

    result = agent.answer(user_message)
    history = history + [{"role": "assistant", "content": result.response}]
    trace_md = _format_trace(result.trace)
    return history, result.trace.pending_action, trace_md


def clear():
    return [], None, "_Trace will appear here after your first message._"


with gr.Blocks(title="Guardrailed Medical Information Agent") as demo:
    gr.Markdown(f"# Guardrailed Medical Information Agent\n{DISCLAIMER}")

    with gr.Row():
        with gr.Column(scale=2):
            chatbot = gr.Chatbot(height=500, label="Conversation")
            msg = gr.Textbox(label="Your message", placeholder="Ask a general medical question...")
            with gr.Row():
                submit_btn = gr.Button("Send", variant="primary")
                clear_btn = gr.Button("Clear")
        with gr.Column(scale=1):
            trace_box = gr.Markdown(
                value="_Trace will appear here after your first message._",
                label="Guardrail trace",
            )

    pending_action_state = gr.State(None)

    submit_btn.click(
        respond, [msg, chatbot, pending_action_state], [chatbot, pending_action_state, trace_box]
    ).then(lambda: "", None, msg)
    msg.submit(
        respond, [msg, chatbot, pending_action_state], [chatbot, pending_action_state, trace_box]
    ).then(lambda: "", None, msg)
    clear_btn.click(clear, None, [chatbot, pending_action_state, trace_box])


if __name__ == "__main__":
    demo.launch()

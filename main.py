"""Interactive CLI for the guardrailed medical information agent."""

import sys

from src import agent

sys.stdout.reconfigure(encoding="utf-8")


def main():
    print("Guardrailed Medical Information Agent (type 'quit' to exit)\n")
    pending_action = None

    while True:
        try:
            user_message = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user_message:
            continue
        if user_message.lower() in {"quit", "exit"}:
            break

        if pending_action is not None:
            if user_message.lower() in {"yes", "y", "confirm"}:
                observation = agent.execute_pending_action(pending_action)
                print(f"\nAssistant: {observation}\n")
            else:
                print("\nAssistant: Okay, cancelled that action.\n")
            pending_action = None
            continue

        result = agent.answer(user_message)
        print(f"\nAssistant: {result.response}\n")

        if result.trace.short_circuited_at:
            print(f"[trace] short-circuited at: {result.trace.short_circuited_at}")
        elif result.trace.pending_action:
            pending_action = result.trace.pending_action
            print(f"[trace] awaiting confirmation for tool: {pending_action.tool_name}")
        else:
            print(f"[trace] initial retrieval: {result.trace.retrieved_ids}")
            for step in result.trace.steps:
                flag = " (FLAGGED AS SUSPICIOUS)" if step.flagged_as_suspicious else ""
                print(f"[trace] tool call: {step.tool_name}({step.arguments}){flag}")
            if result.trace.stopped_at_max_iterations:
                print("[trace] stopped: max iterations reached")
            if result.trace.grounding:
                statuses = [c.status for c in result.trace.grounding.claims]
                print(f"[trace] claim statuses: {statuses}")

        total_latency = sum(result.trace.latency_ms.values())
        print(f"[trace] total added latency: {total_latency:.0f} ms\n")


if __name__ == "__main__":
    main()

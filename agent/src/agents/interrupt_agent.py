@tool(context=True)
def schedule_meeting(topic: str, tool_context: ToolContext, attendee: str = "") -> str:
    """Ask the user to pick a meeting time, then confirm what was scheduled.

    Args:
        topic: Short description of the meeting purpose.
        attendee: Who the meeting is with, if known.
    """
    answer = tool_context.interrupt(
        "schedule_meeting",
        reason={"topic": topic, "attendee": attendee},
    )

    # Neither the envelope nor the value inside it is guaranteed to be a
    # mapping: `ag_ui_strands` wraps a resolved answer as `{"response": ...}`
    # and a cancel as `{"cancelled": True}`, but the payload itself is whatever
    # the client sent, and a client that answers with a bare value would make
    # `answer.get` raise inside the tool. Both levels are checked.
    envelope: Mapping = answer if isinstance(answer, Mapping) else {}
    # `ag_ui_strands` wraps the answer under "response"; a bridge that passes
    # the client payload through (the published TypeScript one does) hands the
    # payload itself, so a mapping without that key IS the payload.
    inner = envelope["response"] if "response" in envelope else envelope
    payload = inner if isinstance(inner, Mapping) else {}
    cancelled = (
        envelope.get("cancelled")
        or envelope.get("status") == "cancelled"
        or payload.get("cancelled")
        or payload.get("status") == "cancelled"
    )
    if cancelled:
        return f"User cancelled. Meeting NOT scheduled: {topic}"

    label = payload.get("chosen_label") or payload.get("chosen_time")
    if not label:
        return f"User did not pick a time. Meeting NOT scheduled: {topic}"
    return f"Meeting scheduled for {label}: {topic}"


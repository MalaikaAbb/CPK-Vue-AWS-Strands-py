# Pausing the Agent for Input

> Pause an agent run, hand control to a custom Vue component, and resume with the user's answer.

## What is this?

`useInterrupt` lets your agent pause mid-run, hand control to the user through custom Vue UI, and resume with whatever the user returns. How that pause is implemented depends on the framework's runtime.



LangGraph ships a first-class [`interrupt()`](https://docs.langchain.com/oss/python/langgraph/interrupts) primitive that lets a running node suspend itself and hand control to the client. The run is frozen server-side until the client resolves the interrupt with a payload, at which point the node resumes as if `interrupt()` had simply returned that payload.

CopilotKit's `useInterrupt` is the frontend half of that contract: it subscribes to the paused run, exposes reactive interrupt state, and resumes the agent with the user's answer.







## When should I use this?

Reach for `useInterrupt` when the pause is a **graph-enforced checkpoint** where the code path _must_ stop and wait for a human, not an LLM-initiated tool call. Typical cases:

- A sensitive action (payments, irreversible writes) must be approved
- A required piece of state isn't known and can only be collected from the user
- The agent explicitly reaches an approval node in a longer workflow
- You want the server-side contract to be `interrupt(...)` and resume with a payload

For LLM-initiated pauses where the model decides on the fly to ask the user, prefer [`useHumanInTheLoop`](../human-in-the-loop).



## The backend: `interrupt()` inside a tool

<Steps>
  <Step>
    ### Pause a tool with Strands' native interrupt

    AWS Strands ships a first-class
    [interrupt primitive](https://strandsagents.com/docs/user-guide/concepts/interrupts/).
    A tool declared with `@tool(context=True)` calls
    `tool_context.interrupt(name, reason=...)`, which halts the agent loop and
    hands `reason` to the client as the interrupt payload. The AG-UI adapter
    finishes the run with `RUN_FINISHED` carrying `outcome.type == "interrupt"`.

    
~~~~python title="src/agents/interrupt_agent.py"
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


~~~~


    The resume payload arrives wrapped: an answer as `{"response": ...}`, a
    client-side cancel as `{"cancelled": True}`. The adapter wraps it because
    Strands' resume gate is truthiness-based, so a bare falsy answer would
    re-raise the same interrupt forever.

  </Step>
  <Step>
    ### Keep the pausing tool off a client-executed name

    `useHumanInTheLoop` registers its tool on the FRONTEND, so a name used
    there cannot also be a pausing backend tool. This showcase mounts a
    dedicated interrupt agent and points the interrupt demos' agent names at
    it, leaving `schedule_meeting` on the shared agent free for the
    frontend-tool flow.

  </Step>
  <Step>
    ### Resume in the same process, or across a restart

    Pause and resume on the same running process need no extra wiring. For a
    resume that survives a restart, give the agent a Strands `SessionManager`
    through `StrandsAgentConfig.session_manager_provider`; the adapter
    persists its interrupt checkpoint into that session.

  </Step>
</Steps>

The agent can expose a `schedule_meeting` tool that issues an interrupt with the meeting context. The run freezes until the client resolves it; the resolution becomes the return value of `interrupt()`, which the tool then interprets for the model.

Two things to note:

- The payload, for example `{ "topic": topic, "attendee": attendee }`, is what the Vue frontend receives as `event.value`. Keep it a plain, serializable object containing the pause-time context the UI needs.
- The return-side contract, such as `{ chosen_label, chosen_time }` or `{ cancelled: true }`, is entirely yours. The client can send any serializable resolve payload; the tool gives it meaning and must validate it before a side effect.

## The frontend: `useInterrupt` and the chat slot

Register `useInterrupt` in a descendant component. With the default `renderInChat: true`, the composable publishes the pending interrupt to `CopilotChat`; render it through the `#interrupt` scoped slot and call `resolve(...)` to resume:

```vue title="src/components/MeetingChat.vue"
<script setup lang="ts">
import { CopilotChat, useInterrupt } from "@copilotkit/vue/v2";

useInterrupt<{ topic: string; attendee: string }>({
  agentId: "gen-ui-interrupt",
});
</script>

<template>
  <CopilotChat agent-id="gen-ui-interrupt">
    <template #interrupt="{ event, resolve }">
      <section>
        <p>Pick a time for {{ (event.value as { topic: string }).topic }}</p>
        <button
          @click="resolve({ chosen_label: 'Tomorrow', chosen_time: '2026-09-01T09:00:00Z' })"
        >
          Tomorrow at 09:00
        </button>
        <button @click="resolve({ cancelled: true })">Cancel</button>
      </section>
    </template>
  </CopilotChat>
</template>
```

Whatever you pass to `resolve` is round-tripped back to the agent as the return value of the matching interrupt.







### Key props

- **`agentId`** — must match a runtime-registered agent. If omitted, the composable assumes the default agent. A mismatch means the interrupt never appears.
- **`renderInChat`** — when `true`, `slotProps` are published to the chat's `#interrupt` slot. Set it to `false` when your own component renders the returned refs elsewhere.
- **`handler`** — optionally preprocesses the interrupt, can resolve it early, and exposes its return value as `result`.
- **`enabled`** — filters interrupt shapes before they are surfaced.

The Vue `#interrupt` slot receives `{ event, result, resolve }`. For the complete standard-interrupt surface — including `interrupt`, `interrupts`, and `cancel` — use the composable's returned `slotProps` with `renderInChat: false`.

## Multiple interrupts? Add a type and gate with `enabled`

If your graph issues more than one kind of interrupt, tag each payload with a `type` field and install one `useInterrupt` per shape, each gated by `enabled`:

```ts
useInterrupt({
  agentId: "gen-ui-interrupt",
  enabled: (event) => (event.value as { type?: string }).type === "ask",
});

useInterrupt({
  agentId: "gen-ui-interrupt",
  enabled: (event) => (event.value as { type?: string }).type === "approval",
});
```

## Preprocess with `handler`

For cases where the interrupt can sometimes be resolved _without_ user input, pass a `handler` that runs before the UI is rendered. The handler can call `resolve(...)` itself to resume the agent early, or return a value exposed as `result`:

```ts
const { slotProps } = useInterrupt({
  agentId: "gen-ui-interrupt",
  renderInChat: false,
  handler: async ({ event, resolve }) => {
    const department = await lookupUserDepartment();
    const required = (event.value as { accessDepartment: string })
      .accessDepartment;

    if (required === department || department === "admin") {
      await resolve({ code: "AUTH_BY_DEPARTMENT" });
      return;
    }

    return { department };
  },
});
```



## AG-UI standard interrupt flow vs. legacy

`useInterrupt` supports two interrupt transports. Understanding which one your agent uses helps you write the right UI.

### Standard flow (`RUN_FINISHED` with `outcome.type === "interrupt"`)

When the agent backend conforms to the AG-UI protocol, it signals an interrupt by emitting a `RUN_FINISHED` event whose outcome carries the interrupts array:

```text
outcome.type === "interrupt"
outcome.interrupts  // Interrupt[]
```

The composable detects this on `onRunFinishedEvent` and exposes the interrupts after `onRunFinalized` fires. `slotProps.value` contains:

- **`interrupt`** — the primary `Interrupt` (`interrupts[0]`), with shape `{ id, reason, message?, toolCallId?, responseSchema?, expiresAt?, metadata? }`.
- **`interrupts`** — the full open set.
- **`resolve(payload?, interruptId?)`** — records a resolved response for the targeted interrupt. The run resumes once every open interrupt has a response.
- **`cancel(interruptId?)`** — records a cancelled response for the targeted interrupt. The same accumulate-then-submit logic applies.

### Legacy flow (`on_interrupt` custom event)

Older agents may emit a custom `on_interrupt` event. The composable exposes its payload in `event.value`, with `interrupt` set to `null` and `interrupts` to `[]`. Calling `resolve(payload)` resumes via `forwardedProps.command`, the legacy mechanism. `cancel()` dismisses the interrupt without resuming because the legacy transport has no cancel response.

### Priority

If both signals appear on the same run, the standard flow wins.

### Approve / Cancel example

```vue title="src/components/ApprovalPanel.vue"
<script setup lang="ts">
import { useInterrupt } from "@copilotkit/vue/v2";

const { slotProps } = useInterrupt({ renderInChat: false });
</script>

<template>
  <section v-if="slotProps">
    <p>{{ slotProps.interrupt?.message ?? "Approve this action?" }}</p>
    <button @click="slotProps.resolve({ approved: true })">Approve</button>
    <button @click="slotProps.cancel()">Cancel</button>
  </section>
</template>
```

Both methods return the `RunAgentResult` once the run restarts, or `void` while waiting for responses to other open interrupts.

### Multi-interrupt behavior

Some agents issue more than one interrupt in a single run. Each interrupt has its own `id`; address them individually:

```vue
<template>
  <ul v-if="slotProps">
    <li v-for="item in slotProps.interrupts" :key="item.id">
      {{ item.message }}
      <button @click="slotProps.resolve({ ok: true }, item.id)">Approve</button>
      <button @click="slotProps.cancel(item.id)">Cancel</button>
    </li>
  </ul>
</template>
```

The agent run resumes only after **every** open interrupt has been addressed. If you omit `interruptId`, the primary interrupt is targeted; Vue warns when several are open.

### `responseSchema` — surface only, no client-side validation

The `Interrupt` type exposes a `responseSchema` JSON Schema that the agent can use to describe the expected payload. `useInterrupt` surfaces it on `interrupt.responseSchema` for your UI to read, but it does **not** validate `resolve` payloads against it. Validation is the agent's responsibility on resume.

## Provider setup

The component calling `useInterrupt` must be a descendant of `CopilotKitProvider`:

```vue title="src/App.vue"
<script setup lang="ts">
import { CopilotKitProvider } from "@copilotkit/vue/v2";
import MeetingChat from "./components/MeetingChat.vue";
</script>

<template>
  <CopilotKitProvider runtime-url="/api/copilotkit">
    <MeetingChat />
  </CopilotKitProvider>
</template>
```

## Going further

- [Tool-based HITL with `useHumanInTheLoop`](../human-in-the-loop) — for LLM-initiated pauses.
- [Headless interrupts](./headless) — render and resolve interrupts outside a chat surface.

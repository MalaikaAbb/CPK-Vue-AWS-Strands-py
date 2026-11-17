# Tool Call Rendering

> Render your agent's tool calls with custom UI components.

## What is this?

Tools are how an LLM invokes predefined, typically-deterministic functions. Tool rendering lets you decide how each of those tool calls appears in the chat. Instead of showing raw JSON, you register a Vue component that draws a branded card for the call (arguments, live status, and the eventual result). This is the **Generative UI** variant CopilotKit calls **tool rendering**.

<Callout type="info">
  **Free course:** See this pattern built end-to-end in [Build Interactive Agents with Generative UI](https://www.deeplearning.ai/short-courses/build-interactive-agents-with-generative-ui/) — a free DeepLearning.AI short course taught by CopilotKit's CEO covering the full Generative UI spectrum (Controlled, Declarative, and Open-Ended).
</Callout>

## When should I use this?

Render tool calls when you want to:

- Show users exactly what tools the agent is invoking and with what arguments
- Display live progress indicators while a tool executes
- Render rich, polished results once a tool completes
- Give tool-heavy agents a transparent, on-brand chat experience

## Default tool rendering (zero-config)

The simplest entry point is `useDefaultRenderTool()` with no arguments. CopilotKit registers its built-in default renderer as the `*` wildcard: every tool call renders as a status card (tool name, live **Running → Done** state, collapsible arguments/result) without you writing any UI.

Without this composable the runtime has no `*` renderer and tool calls are invisible; the user only sees the assistant's final text summary.

```vue title="src/components/AgentExperience.vue"
<script setup lang="ts">
import { CopilotChat, useDefaultRenderTool } from "@copilotkit/vue/v2";

useDefaultRenderTool();
</script>

<template><CopilotChat /></template>
```

## Custom catch-all

Once you want on-brand chrome, pass a `render` component or function to `useDefaultRenderTool`. It's a convenience wrapper around `useRenderTool({ name: "*", ... })`: one wildcard renderer handles every tool call, named or not.

```ts title="src/components/AgentExperience.vue"
useDefaultRenderTool({ render: BrandedToolCard });
```

## Per-tool renderers

The most expressive path is one renderer per tool name. Each renderer receives the tool's parsed arguments, a live `status`, and, once the agent returns, the `result`.

```vue title="src/components/WeatherToolCard.vue"
<script setup lang="ts">
defineProps<{
  parameters: { city?: string };
  status: "inProgress" | "executing" | "complete";
  result?: string;
}>();
</script>

<template>
  <p v-if="status !== 'complete'">Checking {{ parameters.city ?? "…" }}</p>
  <article v-else>
    <strong>{{ parameters.city }}</strong>
    <pre>{{ result }}</pre>
  </article>
</template>
```

```vue title="src/components/AgentExperience.vue"
<script setup lang="ts">
import { z } from "zod";
import { CopilotChat, useDefaultRenderTool, useRenderTool } from "@copilotkit/vue/v2";
import WeatherToolCard from "./WeatherToolCard.vue";

useRenderTool({
  name: "get_weather",
  parameters: z.object({ city: z.string() }),
  render: WeatherToolCard,
});

useDefaultRenderTool(); // wildcard fallback for every other tool
</script>

<template><CopilotChat /></template>
```

`parameters` is partial while arguments stream. Read required fields only after the status advances from `inProgress`. The result is a string when status is `complete`; parse it only if your backend deliberately returns a documented serialized shape.

<Callout type="info">
  The `name` you pass to `useRenderTool` must match the tool name the agent exposes; that's how the runtime routes the call to your component.
</Callout>

Per-tool renderers compose with a catch-all: named renderers claim the "interesting" tools and a wildcard handles everything else. The example registers the built-in wildcard after the named `get_weather` renderer.

If the renderer closes over reactive values, pass Vue watch sources as the second argument:

```ts
useRenderTool({ name: "get_weather", parameters, render: WeatherToolCard }, [locale]);
```

Finally, mount the registration component beneath the provider:

```vue title="src/App.vue"
<script setup lang="ts">
import { CopilotKitProvider } from "@copilotkit/vue/v2";
import AgentExperience from "./components/AgentExperience.vue";
</script>

<template>
  <CopilotKitProvider runtime-url="/api/copilotkit"><AgentExperience /></CopilotKitProvider>
</template>
```

## The backend tool definition

The frontend renderer only sees what the agent sends down. The matching backend must expose a tool named `get_weather`, return structured data, and let the frontend renderer with the same name paint the card. The Vue renderer does not create or execute that backend tool.

<!-- setup skipped: tool-rendering-setup is not bundled for strands -->

```python
# src/agents/agent.py
import json
import logging
import os
import threading
import uuid
from collections.abc import AsyncIterator, Mapping
from contextlib import aclosing
from typing import Any, Optional

from ag_ui.core.types import Context
from ag_ui_strands import (
    StrandsAgent,
    StrandsAgentConfig,
    ToolBehavior,
)
from strands import Agent, tool
from strands.hooks import (
    AfterToolCallEvent,
    BeforeInvocationEvent,
    BeforeToolCallEvent,
    HookProvider,
    HookRegistry,
)
from strands.models.openai import OpenAIModel
from strands.types.tools import ToolContext

# Import shared tool implementations (symlinked at project root → ../../shared/python/tools)
from tools import (
    get_weather_impl,
    query_data_impl,
    roll_dice_impl,
    schedule_meeting_impl,
    search_flights_impl,
)

from tools.todos import BoardTodoInput, manage_todos_impl

# gen-ui-agent specialization (set_steps tool + state hook + prompt addendum).
# The shared Strands backend serves every demo; this module lives in its own
# file so the gen-ui-agent surface area is reviewable in isolation, matching
# the wave-2 BYOC pattern (byoc_hashbrown.py / byoc_json_render.py).
from agents.gen_ui_agent import (
    GEN_UI_AGENT_PROMPT,
    set_steps,
    steps_state_from_args,
)

# Dynamic A2UI generation (`generate_a2ui` + its structured error shape). Its
# own module for the same reason as gen_ui_agent above — and so the docs'
# `backend-render-operations` snippet is that tool rather than all of agent.py.
from agents.a2ui_generate import generate_a2ui
from agents.todo_state_sync import TodoStateAgent, TodoStateHook

logger = logging.getLogger(__name__)


class _StateContextWrapper:
    """Add transient state context and preserve the adapter's event stream."""

    def __init__(self, delegate: StrandsAgent) -> None:
        self._delegate = delegate

    def __getattr__(self, name: str) -> Any:
        return getattr(self._delegate, name)

    async def run(self, input_data: Any) -> AsyncIterator[Any]:
        # The adapter owns snapshots, including unfinished parallel calls.
        async with aclosing(
            self._delegate.run(with_state_context(input_data))
        ) as events:
            async for event in events:
                yield event


# ---- Tools --------------------------------------------------------------


@tool
def get_weather(location: str):
    """Get current weather for a location.

    Args:
        location: The location to get weather for

    Returns:
        Weather information as JSON string
    """
    return json.dumps(get_weather_impl(location))


```

<IntegrationGrid path="generative-ui/tool-rendering" />

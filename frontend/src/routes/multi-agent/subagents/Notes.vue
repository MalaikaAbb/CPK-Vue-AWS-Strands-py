<script setup lang="ts">
import Callout from "@/components/harness/Callout.vue";
import Panel from "@/components/harness/Panel.vue";
import RouteHeader from "@/components/harness/RouteHeader.vue";
import SourceCode from "@/components/harness/SourceCode.vue";
</script>

<template>
  <RouteHeader path="/multi-agent/subagents" />
  <Callout tone="warn" title="Gap: the backend cannot load, and there is no frontend (README §9)">
    <p>· <code>src/agents/agent.py</code> (verbatim below, 594 lines) defines the <code>research_agent</code> / <code>writing_agent</code> / <code>critique_agent</code> delegation tools among many others, but imports five modules no page publishes (<code>tools</code>, <code>tools.todos</code>, <code>agents.gen_ui_agent</code>, <code>agents.a2ui_generate</code>, <code>agents.todo_state_sync</code>), so it cannot be imported. Per your rules nothing was written in their place; the file is not served.</p>
    <p>· The “Rendering a live delegation log” section publishes no Vue code, so this route has no demo.</p>
  </Callout>
  <Panel title="Published backend, verbatim, not served"><SourceCode file="agent/src/agents/agent.py" /></Panel>
</template>

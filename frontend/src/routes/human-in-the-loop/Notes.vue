<script setup lang="ts">
import Callout from "@/components/harness/Callout.vue";
import Panel from "@/components/harness/Panel.vue";
import PublishedCode from "@/components/harness/PublishedCode.vue";
import RouteHeader from "@/components/harness/RouteHeader.vue";
import SourceCode from "@/components/harness/SourceCode.vue";
import TryIt from "@/components/harness/TryIt.vue";
</script>

<template>
  <RouteHeader path="/human-in-the-loop" />
  <Panel title="What it demonstrates">
    <p class="text-sm leading-relaxed text-slate-700 dark:text-slate-300">
      Pattern 1: <code>useHumanInTheLoop</code> registers <code>schedule_meeting</code>. When the model calls it, the render component gets a
      <code>respond</code> callback while the call is executing, and the run resumes with the user's answer as the tool result.
    </p>
    <div class="mt-4">
      <TryIt :prompts="['Schedule a meeting about Q3 planning with Dana']" expect="A card with topic and attendee and three time slots; picking one resumes the run and the agent confirms that time." fail="A prose answer and no card, or a card that never resumes the run." />
    </div>
  </Panel>
  <Panel title="Published file, mounted verbatim"><SourceCode file="frontend/src/routes/human-in-the-loop/demo-chat/components/MeetingApproval.vue" /></Panel>
  <Callout tone="harness" title="What the harness added">
    <p>· <strong>TimePickerCard.vue</strong> — imported by the page, never published. Without it the tool has no UI and never calls <code>respond</code>. Minimal stand-in: three fixed slots (the page mentions “static candidate slots”), plus “None of these”.</p>
    <p>· <strong>HarnessApp.vue</strong> — the page prints no App.vue; this mounts MeetingApproval beside a CopilotChat under the standard provider.</p>
  </Callout>
  <Panel title="Harness files">
    <div class="space-y-4">
      <SourceCode file="frontend/src/routes/human-in-the-loop/demo-chat/components/TimePickerCard.vue" />
      <SourceCode file="frontend/src/routes/human-in-the-loop/demo-chat/HarnessApp.vue" />
    </div>
  </Panel>
  <Panel title="Also published: interrupt_agent.py — runs on the interrupt routes, not here"><SourceCode file="agent/src/agents/interrupt_agent.py" note="A pausing schedule_meeting tool. The page says it belongs to a dedicated interrupt agent, keeping schedule_meeting on the shared agent free for this frontend-tool flow — so this route's default stays the Quickstart agent, and gen-ui-interrupt / interrupt-headless run it (agent/harness_app.py, flagged)." /></Panel>
  <Callout tone="info" title="Pattern 2"><p><code>useInterrupt</code> is on its own route, <a href="/human-in-the-loop/useInterrupt" class="underline">Pausing the Agent for Input</a>.</p></Callout>
</template>

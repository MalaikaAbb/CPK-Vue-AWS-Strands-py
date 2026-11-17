<script setup lang="ts">
import Callout from "@/components/harness/Callout.vue";
import Panel from "@/components/harness/Panel.vue";
import PublishedCode from "@/components/harness/PublishedCode.vue";
import RouteHeader from "@/components/harness/RouteHeader.vue";
import SourceCode from "@/components/harness/SourceCode.vue";
import TryIt from "@/components/harness/TryIt.vue";
const D = "frontend/src/routes/human-in-the-loop/useInterrupt/demo-chat";
</script>

<template>
  <RouteHeader path="/human-in-the-loop/useInterrupt" />
  <Panel title="What it demonstrates">
    <p class="text-sm leading-relaxed text-slate-700 dark:text-slate-300">
      <code>MeetingChat.vue</code> renders a pending interrupt in <code>CopilotChat</code>'s <code>#interrupt</code> slot (agent
      <code>gen-ui-interrupt</code>), with buttons that <code>resolve</code> it; <code>ApprovalPanel.vue</code> renders the same state
      outside the transcript with <code>renderInChat: false</code>.
    </p>
    <div class="mt-4">
      <TryIt :prompts="['Schedule a meeting about Q3 planning']" expect="If the agent interrupted: “Pick a time for …” with Tomorrow at 09:00 / Cancel; resolving resumes the run." fail="A normal reply and no picker — check the agent runs harness_app.py (it serves /interrupt), not main.py." />
    </div>
  </Panel>
  <Panel title="Published files, mounted verbatim">
    <div class="space-y-4">
      <SourceCode :file="`${D}/components/MeetingChat.vue`" />
      <SourceCode :file="`${D}/components/ApprovalPanel.vue`" />
      <SourceCode :file="`${D}/App.vue`" />
    </div>
  </Panel>
  <Panel title="Published, not mounted">
    <div class="space-y-4">
      <PublishedCode page="human-in-the-loop__useInterrupt" :index="2" note="Fragment: two enabled-gated registrations with no component around them." />
      <PublishedCode page="human-in-the-loop__useInterrupt" :index="3" note="Fragment: lookupUserDepartment is never defined." />
      <PublishedCode page="human-in-the-loop__useInterrupt" :index="6" note="Fragment: reads slotProps from a call it does not print." />
    </div>
  </Panel>
  <Callout tone="info" title="The backend (README §9.5)">
    <p>The page publishes <code>interrupt_agent.py</code>: a <code>schedule_meeting</code> tool that calls <code>tool_context.interrupt(...)</code> and reads the answer as <code>{"response": …}</code> / <code>{"cancelled": True}</code>, which matches what <code>MeetingChat.vue</code> resolves with. The page also says the showcase mounts a dedicated interrupt agent for the interrupt demos' agent names, keeping <code>schedule_meeting</code> on the shared agent free for the frontend-tool flow.</p>
  </Callout>
  <Callout tone="harness" title="Agent id"><p><code>gen-ui-interrupt</code> → the interrupt agent at <code>/interrupt</code> (<code>backend/agents.ts</code> → <code>agent/harness_app.py</code>). The page publishes <code>MeetingChat.vue</code>, so no stand-in is needed.</p></Callout>
  <Panel title="The page's backend — interrupt_agent.py (verbatim)"><SourceCode file="agent/src/agents/interrupt_agent.py" note="Published on HITL Overview and useInterrupt: the schedule_meeting tool only, with no imports and no Agent." /></Panel>
  <Panel title="Harness — agent/harness_app.py (flagged, at your request: “Imports + agent”)"><SourceCode file="agent/harness_app.py" note="Runs the verbatim file with the three names it never imports (tool, ToolContext, Mapping), builds an Agent from the Quickstart's model and prompt plus tools=[schedule_meeting], and mounts it at /interrupt next to the Quickstart's app." /></Panel>
</template>

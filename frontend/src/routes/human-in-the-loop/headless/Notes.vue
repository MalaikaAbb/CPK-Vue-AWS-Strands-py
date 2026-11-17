<script setup lang="ts">
import Callout from "@/components/harness/Callout.vue";
import Panel from "@/components/harness/Panel.vue";
import PublishedCode from "@/components/harness/PublishedCode.vue";
import RouteHeader from "@/components/harness/RouteHeader.vue";
import SourceCode from "@/components/harness/SourceCode.vue";
import TryIt from "@/components/harness/TryIt.vue";
const D = "frontend/src/routes/human-in-the-loop/headless/demo-chat";
</script>

<template>
  <RouteHeader path="/human-in-the-loop/headless" />
  <Panel title="What it demonstrates">
    <p class="text-sm leading-relaxed text-slate-700 dark:text-slate-300">
      Interrupts with no chat mounted: <code>HeadlessInterruptPanel</code> starts a run on agent <code>interrupt-headless</code> with
      <code>agent.addMessage</code> + <code>copilotkit.runAgent</code>, then shows Approve / Cancel when the run pauses.
    </p>
    <div class="mt-4">
      <TryIt :prompts="['Click Start']" expect="If the agent interrupted: the interrupt message with Approve / Cancel; Approve resumes the run." fail="What actually happens here: the run finishes and the Start button comes back (see below)." />
    </div>
  </Panel>
  <Panel title="Published files, mounted verbatim">
    <div class="space-y-4">
      <SourceCode :file="`${D}/components/HeadlessInterruptPanel.vue`" />
      <SourceCode :file="`${D}/App.vue`" />
      <SourceCode :file="`${D}/components/ApprovalPanel.vue`" note="Published on this page; App.vue does not mount it." />
    </div>
  </Panel>
  <Callout tone="warn" title="Why no interrupt is expected (README §9.5)">
    <p>This page publishes no backend. HITL Overview and useInterrupt publish <code>interrupt_agent.py</code> and say the showcase points the interrupt demos' agent names at a dedicated interrupt agent, so <code>interrupt-headless</code> runs it. Its only pausing tool is <code>schedule_meeting</code>, while Start sends “Prepare the governed action.”, so the model has no reason to call it. Nothing was changed to force the interrupt.</p>
  </Callout>
  <Callout tone="harness" title="Agent id"><p><code>interrupt-headless</code> → the interrupt agent at <code>/interrupt</code> (<code>backend/agents.ts</code> → <code>agent/harness_app.py</code>), per the useInterrupt page's “interrupt demos' agent names”. The page publishes both panels, so no stand-in is needed.</p></Callout>
  <Panel title="The page's backend — interrupt_agent.py (verbatim)"><SourceCode file="agent/src/agents/interrupt_agent.py" note="Published on HITL Overview and useInterrupt: the schedule_meeting tool only, with no imports and no Agent." /></Panel>
  <Panel title="Harness — agent/harness_app.py (flagged, at your request: “Imports + agent”)"><SourceCode file="agent/harness_app.py" note="Runs the verbatim file with the three names it never imports (tool, ToolContext, Mapping), builds an Agent from the Quickstart's model and prompt plus tools=[schedule_meeting], and mounts it at /interrupt next to the Quickstart's app." /></Panel>
</template>

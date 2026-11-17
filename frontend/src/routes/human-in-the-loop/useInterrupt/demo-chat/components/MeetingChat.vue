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

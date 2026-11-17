<script setup lang="ts">
import { toRaw } from "vue";
import { useAgent, useCopilotKit, useInterrupt } from "@copilotkit/vue/v2";

const { agent } = useAgent({ agentId: "interrupt-headless" });
const { copilotkit } = useCopilotKit();
const { slotProps } = useInterrupt({
  agentId: "interrupt-headless",
  renderInChat: false,
});

async function kickOff(prompt: string) {
  const current = agent.value;
  if (!current || current.isRunning) return;

  current.addMessage({
    id: crypto.randomUUID(),
    role: "user",
    content: prompt,
  });
  await copilotkit.value.runAgent({ agent: toRaw(current) });
}
</script>

<template>
  <section v-if="slotProps">
    <p>{{ slotProps.interrupt?.message ?? "Pick an option" }}</p>
    <button @click="slotProps.resolve({ choice: 'approve' })">Approve</button>
    <button @click="slotProps.cancel()">Cancel</button>
  </section>
  <button v-else @click="kickOff('Prepare the governed action.')">
    Start
  </button>
</template>

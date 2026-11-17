<script setup lang="ts">
import { useInterrupt } from "@copilotkit/vue/v2";

const { slotProps } = useInterrupt({
  agentId: "interrupt-headless",
  renderInChat: false,
});
</script>

<template>
  <section v-if="slotProps" class="approval-panel">
    <p>{{ slotProps.interrupt?.message ?? "Approve this action?" }}</p>
    <button @click="slotProps.resolve({ approved: true })">Approve</button>
    <button @click="slotProps.cancel()">Cancel</button>
  </section>
</template>

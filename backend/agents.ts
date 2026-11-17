import { HttpAgent } from "@ag-ui/client";

/**
 * Agents for every runtime in this repo.
 *
 * `myAgent()` is the agent the Strands landing page registers
 * (https://docs.copilotkit.ai/vue/strands — its only code block), verbatim:
 * an AG-UI HttpAgent pointed at AGENT_URL, where the Strands Quickstart's
 * FastAPI app (agent/main.py: StrandsAgent + create_strands_app) serves the
 * agent.
 *
 * [harness] Doc agent ids. The landing page registers only `my_agent`, while
 * the Vue samples use `default` (no agent-id) and ids no page registers. Every
 * id is the landing page's my_agent, unchanged, except the two interrupt ids:
 * HITL Overview and useInterrupt publish interrupt_agent.py and say the
 * showcase "points the interrupt demos' agent names at" a dedicated interrupt
 * agent. That agent is mounted by agent/harness_app.py at /interrupt (flagged,
 * at the user's request: "Imports + agent"). src/agents/agent.py imports five
 * unpublished modules and cannot load, so it is not served as a whole; its
 * `get_weather` tool runs on harness_app.py's /tool-rendering, reached through
 * its own runtime path (toolRenderingAgent, runtimes/tool-rendering.ts).
 */
export function myAgent() {
  // Verbatim from the landing page's runtime route.
  return new HttpAgent({ url: process.env.AGENT_URL! });
}

/** [harness] The landing page's HttpAgent, pointed at harness_app.py's /interrupt. */
export function interruptAgent() {
  return new HttpAgent({ url: new URL("interrupt", process.env.AGENT_URL!).toString() });
}

/** Doc agent ids that run the interrupt agent (the interrupt demos). */
const INTERRUPT_IDS = new Set(["gen-ui-interrupt", "interrupt-headless"]);

/** [harness] The landing page's HttpAgent, pointed at harness_app.py's /tool-rendering (Tool Rendering's get_weather agent). */
export function toolRenderingAgent() {
  return new HttpAgent({ url: new URL("tool-rendering", process.env.AGENT_URL!).toString() });
}

/** Doc agent ids, and the page each one comes from. */
export const DOC_AGENT_IDS = {
  default: "no agent-id: Quickstart, Slots, Frontend Tools, Components as Tools, Tool Rendering, …",
  "my-agent": "Prebuilt Components, Headless UI, Headless Threads",
  sales: "Programmatic Control",
  support: "Threads Drawer",
  "gen-ui-interrupt": "Pausing the Agent for Input (MeetingChat.vue)",
  "interrupt-headless": "Headless Interrupts",
  researcher: "State Rendering",
  workspace: "Shared State",
  writer: "State Streaming",
} as const;

export function docAgents() {
  return Object.fromEntries(
    Object.keys(DOC_AGENT_IDS).map((id) => [id, INTERRUPT_IDS.has(id) ? interruptAgent() : myAgent()]),
  );
}

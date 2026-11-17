# CopilotKit Vue + AWS Strands (Python) Test Suite

A navigable, working test harness for CopilotKit's **Vue** frontend against an **AWS Strands (Python)** agent. Each Vue doc page is a route that runs that page's own code.

| | |
|---|---|
| **Doc sync date** | Machine-maintained: `doc-snapshot/manifest.json` → `syncedAt` (baseline taken 2026-11-13, 22 pages; the nine Generative UI › Components pages added 2026-11-17, 31 in all). |
| **CopilotKit packages** | `@copilotkit/vue` 1.87.0 · `@copilotkit/core` 1.87.0 · `@copilotkit/runtime` 1.87.0 · `@ag-ui/client` 1.0.2 (`HttpAgent`, the same copy the runtime uses) |
| **Strands** | `strands-agents[OpenAI]` 1.64.0 · `ag-ui-strands` 1.0.4 · `fastapi` 0.162.5 · Python 3.14 (uv default; the Quickstart pins none) |
| **Frontend** | Vite 8.3 · Vue 3.5 · vue-router 5.5 · TypeScript 6.0 · Tailwind 4.3 (harness chrome only) · zod 3.25.76 · chart.js 4.6.1 · maplibre-gl 5.24.1 (Components pages) |
| **Build status** | No CI. `vite build` ✅. `vue-tsc` reports 9 errors, all in published doc code (§9.9). All 86 URLs (every route and every demo sample, Components pages included) mounted in headless Chrome with **zero console or page errors** (2026-11-17). The chain (runtime → `HttpAgent` → Strands agent → OpenAI) was driven with a **fake** key, a frontend tool and context: the run reached OpenAI and failed only with `401 Incorrect API key`. **No route has been driven against a live model yet.** |

---

## 2. Overview

Strands is AWS's Python agent SDK. CopilotKit reaches a Strands agent over AG-UI: the `ag-ui-strands` adapter (`StrandsAgent` + `create_strands_app`) serves the agent as a FastAPI endpoint, the Copilot Runtime registers an AG-UI `HttpAgent` pointed at it, and `@copilotkit/vue` renders the conversation, tools, state and interrupts.

This repo turns the Quickstart and the Basics, Generative UI, Interactivity and Agent capabilities sections of the Vue Strands sidebar (22 pages) into one navigable Vite app. It adds the nine **Generative UI › Components** pages, which aren't under `/vue` and print each sample for React, Angular, React Native and Vue; only their Vue tab is used. Every route mounts the page's code verbatim, bugs included, and shows the exact files that run. Anything the harness added is marked **[harness]** in the file, in a pink **Harness** callout on the notes page, and, for stand-in components, with a **HARNESS STAND-IN** badge on screen.

Tracks: **<https://docs.copilotkit.ai/vue/strands>** and **<https://docs.copilotkit.ai/strands/generative-ui/components>**

---

## 3. Architecture

```
Browser — Vite dev server · localhost:5173
  │  @copilotkit/vue/v2; each /<route>/demo-chat mounts that page's own App.vue
  │  runtime-url="/api/copilotkit…" ──► Vite proxy /api → :8200
  ▼
Node · backend/server.ts · localhost:8200
  │  Vue Quickstart's host: createServer + createCopilotNodeListener({ cors: true })
  │  Strands landing page's runtime: my_agent = new HttpAgent({ url: AGENT_URL })
  │  /api/copilotkit           doc agent ids → my_agent; gen-ui-interrupt, interrupt-headless → AGENT_URL/interrupt
  │  /api/copilotkit-threads   Intelligence quickstart's runtime (if key set)  [harness: own path]
  │  /api/copilotkit-mcp-apps  MCP Apps' runtime (mcpApps.servers)            [harness: own path]
  │  /api/copilotkit-tool-rendering  Tool Rendering's runtime: default → AGENT_URL/tool-rendering  [harness: own path]
  ▼  AGENT_URL (AG-UI over HTTP)
Python · agent/harness_app.py · localhost:8000   (uv)   [harness: imports main.app unchanged]
  │  /           Strands Quickstart (main.py): Agent(OpenAIModel("gpt-6-luna") + [harness] reasoning_effort="none", §9.16) → StrandsAgent → create_strands_app(…, "/")
  │  /interrupt  [harness, flagged] same model + prompt, tools=[schedule_meeting] from src/agents/interrupt_agent.py
  │  /tool-rendering  [harness, flagged] same model + prompt, tools=[get_weather] from src/agents/agent.py (+ get_weather_impl stand-in)
  ▼
OpenAI                                    MCP Apps example server on :3101 (MCP Apps route only)
```

**Three processes.** The agent is **Python** (Strands + FastAPI). The Copilot Runtime is **TypeScript on Node** (`tsx`). The frontend is Vite.

**Where each piece comes from.**
- **The Vue Strands Quickstart redirects to a landing page.** Its `.md` is the Vue (built-in agent) Quickstart, which says to keep its Vue frontend steps and take "the runtime wiring" from your framework's quickstart. So `App.vue`, `main.ts` and the Node host come from the Vue Quickstart.
- **The landing page's only code block is the runtime**, published as a Next.js route: `agents: { my_agent: new HttpAgent({ url: process.env.AGENT_URL! }) }`. It's used verbatim, hosted in the Vue Quickstart's Node listener.
- **The agent** is the Strands Quickstart's (`/strands/quickstart`, linked as the landing page's guide): "Use an existing agent", Python, the OpenAI variant its `uv add … "strands-agents[OpenAI]"` line installs. That's `main.py` verbatim, plus one flagged line (`reasoning_effort`, §9.16).

### Agent ids

The landing page registers only `my_agent`. The Vue samples use `default` (no agent-id), `my-agent`, `sales`, `support`, `gen-ui-interrupt`, `interrupt-headless`, `researcher`, `workspace` and `writer`. Every id is `my_agent` (`backend/agents.ts`), except the two interrupt ids. HITL Overview and useInterrupt publish `src/agents/interrupt_agent.py` (a pausing `schedule_meeting` tool, no imports, no agent) and say the showcase "mounts a dedicated interrupt agent and points the interrupt demos' agent names at it". At your request ("Imports + agent"), `agent/harness_app.py` (flagged) runs the verbatim file with its three missing names and serves it at `/interrupt`; `gen-ui-interrupt` and `interrupt-headless` point there (§9.5). The other page backend (`src/agents/agent.py`) can't load (§9.3). The Components samples keep `runtime-url="/api/copilotkit"` as published, so they run on `default` too (the ms-agent-py choice; §9.15).

### What the adapter does for you (verified in the installed `ag-ui-strands` source)

- **Frontend tools:** `StrandsAgent` syncs every tool in the run's `tools` into the agent's tool registry as a proxy (`sync_proxy_tools`), so the Quickstart agent can call `useFrontendTool`, `useComponent` and `useHumanInTheLoop` tools with no change to `main.py`.
- **Context:** it renders the run's `context` into the model prompt (`_format_agui_context`), so `useAgentContext` values reach the model.
- **Generative UI › Components:** the runtime adds `render_ui` to the run's tools and its guide to the run's context, so both reach the model by the two paths above. Checked by capturing the model request with a fake key (§9.15).
- **Interrupts:** only on the interrupt agent (`/interrupt`), through `schedule_meeting`'s `tool_context.interrupt(...)`.
- **Not provided:** other backend tools and writes to shared state. The Quickstart agent has none, and no loadable page publishes them.

---

## 4. Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Node.js | **24.12+** (or 22.18+) | `create-vue`'s scaffold requires it. Developed on 24.16. |
| npm | 10+ | Developed on npm 12. |
| uv | 0.11+ | Runs the agent (`uv run harness_app.py`). |
| Python | 3.10+ | uv picks one; developed on 3.14. |
| OpenAI API key | — | Required, in `agent/.env`. The agent uses `gpt-6-luna` as published. |
| CopilotKit Intelligence key | — | Optional, only for the two Threads routes. |

---

## 5. Setup

```bash
git clone <this-repo> aws-strands-py && cd aws-strands-py
cd agent && uv sync && cd ..
cd backend && npm install && cd ..
cd frontend && npm install && cd ..
cp .env.example agent/.env              # set OPENAI_API_KEY
cp .env.example backend/.env            # AGENT_URL is pre-filled
```

| File | Variable | What it does |
|---|---|---|
| `agent/.env` | `OPENAI_API_KEY` | **Required.** Read by `main.py` and `harness_app.py` (`os.getenv`). |
| `backend/.env` | `AGENT_URL` | **Required.** The landing page's `HttpAgent` URL: `http://localhost:8000/`. |
| `backend/.env` | `CPK_INTELLIGENCE_API_KEY` | Optional. Intelligence for the Threads runtime: `cd backend && npx copilotkit@latest login && npx copilotkit@latest project select`. |
| `backend/.env` | `APP_USER_ID` · `MCP_APPS_URL` · `PORT` · `COPILOTKIT_TELEMETRY_DISABLED` | Optional: fixed local Threads identity (default `local-user`), MCP server URL (default `http://localhost:3101/mcp`), runtime port (default 8200), telemetry opt-out. |

**Ports:** agent **8000** (hard-coded in the Quickstart's `main.py`), runtime **8200**, frontend **5173** (`strictPort`), MCP Apps example **3101**.

---

## 6. Running the project

```bash
# 1 — Strands agent: the Quickstart's app plus /interrupt and /tool-rendering (--env-file supplies OPENAI_API_KEY)
cd agent && uv run --env-file .env harness_app.py
```
Success: `Uvicorn running on http://0.0.0.0:8000`. (`uv run main.py`, the Quickstart's own command, also works but serves neither `/interrupt` nor `/tool-rendering`, so the two interrupt routes and Tool Rendering fail with `HTTP 404`.) **If port 8000 is taken:** `uv run --env-file .env uvicorn harness_app:app --port 8001`, then set `AGENT_URL=http://localhost:8001/` in `backend/.env`. A `FutureWarning` about implicit wildcard CORS comes from the Quickstart's `create_strands_app` call and is harmless.

```bash
# 2 — Copilot Runtime
cd backend && npm run dev
```
Success:
```
Copilot Runtime listening at http://localhost:8200/api/copilotkit
  Agent: http://localhost:8000/
  + /api/copilotkit-threads  (sse)
  + /api/copilotkit-mcp-apps
  + /api/copilotkit-tool-rendering
```

```bash
# 3 — Vue app
cd frontend && npm run dev               # → http://localhost:5173/
```

Open **<http://localhost:5173>**. The landing page's **Connection** panel probes the runtime paths. **MCP Apps route only:** `cd backend && npm run mcp:apps`.

---

## 7. What to expect: walkthrough per section

Each route has a notes page (`/<route>`: notes, Try-it prompts with pass/fail, the exact source, unmounted samples as published, Harness and gap callouts) and a demo (`/<route>/demo-chat`; a **Sample** picker where a page has several samples).

### Getting Started
**`/quickstart`**: **Try:** `Hello! What can you do?` **Pass:** a streamed reply. **Fail:** connection refused or `RUN_ERROR` means the agent isn't running or `AGENT_URL` is wrong (an HTTP 404 means another server is on that port, §6). A 401 means `OPENAI_API_KEY` is missing from `agent/.env`.

### Basics
**`/prebuilt-components`**, **`/custom-look-and-feel/headless-ui`**, **`/programmatic-control`**: chat against `my_agent`: a streamed reply. Headless UI streams into bare rows. Programmatic Control's default sample adds a chat (harness, on request). **`/custom-look-and-feel/slots`**: nine samples; the **Disclaimer** sample shows no disclaimer (doc bug, §9.10).
**`/prebuilt-components/copilot-threads-drawer`**, **`/headless-threads`**: need `CPK_INTELLIGENCE_API_KEY`. `/api/copilotkit-threads/info` should report `mode: "intelligence"`.
**`/frontend-tools`**: **Try:** `Only show sev1 incidents`. **Pass:** "Current filter" changes to `sev1` and the agent confirms.

### Generative UI
**`/generative-ui/tool-based`**: **Try:** `Show me the weather in Paris`. **Pass:** an inline WeatherCard.
**`/generative-ui/tool-rendering`**: runs on its own runtime path, whose `default` is the page's `get_weather` with a stand-in `get_weather_impl` (§9.3). **Try:** `What's the weather in Paris?` **Pass:** zero-config shows a `get_weather` card ending "Done"; per-tool shows the JSON result (its heading stays empty: the card reads `parameters.city`, but the tool's argument is `location`, a doc bug); catch-all shows the BrandedToolCard stand-in with the result. **Fail:** a prose answer with no tool call means the agent is `main.py`, not `harness_app.py`.
**`/generative-ui/state-rendering`**: **Expected now:** "Idle" (no backend published, §9.4).
**`/generative-ui/mcp-apps`**: needs `npm run mcp:apps`. **Try:** `What time is it on the server?` **Pass:** a tool call, then an inline iframe app.

### Generative UI › Components (Vue tab of the `/strands/generative-ui/components` pages)
All run on `default`, the Quickstart agent, which receives both the `render_ui` tool and its guide (§9.15). Whether the model renders well is not yet checked against a live model.
**`/generative-ui/components`**: the overview's `App.vue` with the standard catalog. It calls `:8200` directly, as published. **Try:** `Compare the Starter, Team, and Enterprise plans in a table`. **Pass:** a table component in the chat.
**`/generative-ui/components/catalogs`**: your own catalog (`ProductGrid`, `ProductCard`). **Try:** `Show me two products`. **Pass:** a grid of product cards.
**`/generative-ui/components/surfaces`**: a page target (`featured`) above the chat; its default content is a **stand-in** `ProductRow`. **Pass:** the agent replaces it with a ProductGrid.
**`/generative-ui/components/standard-catalog`**: the standard catalog, and a sample that replaces `Card` with `MyCard`.
**`/generative-ui/components/state-and-actions`**: `ProductCard` with "Add to cart" (an `onAddToCart` event bound to an `addToCart` function). The handler sample needs `./cart-store`, which isn't published, so clicking takes the card's error path.
**`/generative-ui/components/theming`**: standard components in the amber accent and 10px radius.
**`/generative-ui/components/transports`**: tool, markdown and `agentIds: ['shop']` samples.
**`/generative-ui/components/markdown-mode`**: the guide travels in context, which the adapter puts in the prompt, so the agent can answer with `a2ui` blocks. The `sendContext: false` sample puts the guide only in forwarded props, which no published Strands code reads; the captured request carried no guide.
**`/generative-ui/components/from-a2ui`**: the "After" provider; `Airport` and `Arrow` are **stand-ins**.

### Interactivity
**`/shared-state`**: **Try:** **Prefer concise answers**. **Pass:** `preferences.tone` appears in the agent state (Inspector › State). The notes list stays empty (§9.4).
**`/shared-state/rendering-in-app`**: the Canvas shows "Project launch", but the agent can't edit it (§9.4).
**`/shared-state/streaming`**: **Expected now:** "Waiting for a draft…" throughout (§9.4).
**`/shared-state/agent-readonly`**: **Try:** `Which workspace am I in?` **Pass:** "northstar".
**`/human-in-the-loop`**: **Try:** `Schedule a meeting about Q3 planning with Dana`. **Pass:** a time-picker card (flagged stand-in); picking a slot resumes the run.
**`/human-in-the-loop/governed-actions`**: **Try:** `Refund $40 to customer 1182. Call approve_governed_action first with id a-1, tool send_refund, reference POL-7, verdict require_approval.` **Pass:** an approval card.
**`/human-in-the-loop/useInterrupt`**: **Try:** `Schedule a meeting about Q3 planning`. **Pass:** "Pick a time for …" with Tomorrow at 09:00 / Cancel; Tomorrow resumes the run and the agent confirms the time, Cancel makes it report the meeting was not scheduled. **Fail:** a prose reply and no picker means the agent is running `main.py` instead of `harness_app.py`, or the model didn't call the tool.
**`/human-in-the-loop/headless`**: **Expected now:** no interrupt. Start asks for a governed action, and the interrupt agent's only pausing tool is `schedule_meeting` (§9.5).
**`/webmcp`**: stand-in sample only (your choice). In Chrome 149+ with WebMCP, **Run tool** `searchOrders` `{"status":"open"}` returns ORD-1001 and ORD-1004.

### Agent capabilities
**`/multi-agent/subagents`**: notes only (§9.3).

---

## 8. Testing checklist / current status

| Doc page | Route | Status | Notes |
|---|---|---|---|
| `/vue/strands` | `/` | 📖 Reference | Landing page. |
| `/vue/strands` (Quickstart) | `/quickstart` | ✅ Working | Chain verified with a fake key (OpenAI 401). |
| `prebuilt-components` | same | ✅ Working | Only `CopilotChat` has code. |
| `custom-look-and-feel/slots` | same | ⚠️ Partial | Imports added to fragments; 2 stand-ins; `labels` type error; disclaimer never renders (§9.9, §9.10). |
| `custom-look-and-feel/headless-ui` | same | ✅ Working | |
| `programmatic-control` | same | ✅ Working | Default sample adds a harness chat (on request). |
| `prebuilt-components/copilot-threads-drawer` | same | ⚠️ Partial | Intelligence quickstart runtime, fixed local identity; needs a key (§9.7). |
| `headless-threads` | same | ⚠️ Partial | Same runtime (§9.7). |
| `frontend-tools` | same | ✅ Working | Adapter proxies the tool. Not yet run against a live model. |
| `generative-ui/tool-based` | same | ✅ Working | Same. |
| `generative-ui/tool-rendering` | same | ⚠️ Partial | Published `get_weather` + flagged `get_weather_impl` stand-in on `/tool-rendering`, own runtime path; fake-key run rendered all three samples; per-tool card reads `city` (doc bug); not driven live (§9.3). |
| `generative-ui/state-rendering` | same | ❌ Broken | No backend published (§9.4). |
| `generative-ui/mcp-apps` | same | ⚠️ Partial | Needs `npm run mcp:apps`; placeholder URL replaced (§9.8). |
| `/strands/generative-ui/components` | same | ⚠️ Partial | `App.vue` verbatim + chart/map plugins; tool + guide reach the model (captured); not driven live (§9.15). |
| `…/components/surfaces` | same | ⚠️ Partial | `ProductRow` stand-in; not driven live. |
| `…/components/catalogs` | same | ⚠️ Partial | Provider line wrapped with a chat; fake-key run captured `render_ui` + guide; not driven live. |
| `…/components/standard-catalog` | same | ⚠️ Partial | Not driven live. |
| `…/components/state-and-actions` | same | ⚠️ Partial | `./cart-store` never published; not driven live. |
| `…/components/theming` | same | ⚠️ Partial | Not driven live. |
| `…/components/transports` | same | ⚠️ Partial | Tool and markdown: tool/guide reach the model; not driven live. |
| `…/components/markdown-mode` | same | ⚠️ Partial | Guide reaches the model via context; the `sendContext: false` sample sends none (§9.15). |
| `…/components/from-a2ui` | same | ⚠️ Partial | `Airport`/`Arrow` stand-ins; not driven live. |
| `shared-state` | same | ⚠️ Partial | Read + tone write-back; nothing writes `notes` (§9.4). |
| `shared-state/rendering-in-app` | same | ⚠️ Partial | Canvas renders; agent can't write (§9.4). |
| `shared-state/streaming` | same | ❌ Broken | No backend published (§9.4). |
| `shared-state/agent-readonly` | same | ✅ Working | Adapter injects context into the prompt. |
| `human-in-the-loop` | same | ⚠️ Partial | Proxied tool; `TimePickerCard` stand-in. |
| `human-in-the-loop/useInterrupt` | same | ⚠️ Partial | Page's `interrupt_agent.py` in a flagged harness agent at `/interrupt`; fake-key run reaches OpenAI; not yet driven live (§9.5). |
| `human-in-the-loop/headless` | same | ❌ Broken | Runs the interrupt agent, but Start's prompt doesn't fit its only pausing tool (§9.5). |
| `human-in-the-loop/governed-actions` | same | ⚠️ Partial | Tool half proxied; interrupt half §9.5; `executeSideEffect` undefined. |
| `webmcp` | same | ⚠️ Partial | Stand-in sample only; as published every call errors (§9.6). |
| `multi-agent/subagents` | same | ❌ Broken | Backend can't load; no Vue code (§9.3). |

**Legend:** ✅ Working · ⚠️ Partial · 📖 Reference · 🚧 Not started · ❌ Broken. "Working" means wired and verified from code, mounts, and the fake-key run; **not yet driven against a live model.**

---

## 9. Known issues / doc-vs-implementation discrepancies

All against `@copilotkit/vue` / `@copilotkit/runtime` 1.87.0, `ag-ui-strands` 1.0.4, and the docs as of the 2026-11-13 baseline.

**1. The Quickstart is split across three pages.** `/vue/strands/quickstart` redirects (307) to the landing page. The root `.md` is the built-in Vue Quickstart (`BuiltInAgent`), rendered on `/vue`. The landing page renders a single code block, the runtime route, which appears in no `.md`. The agent is on the non-Vue `/strands/quickstart` "Use an existing agent" tab, which renders client-side (verified through `data-raw-code`). That page offers OpenAI and Anthropic variants; this repo uses the OpenAI `main.py`, matching its `strands-agents[OpenAI]` install line.

**2. The runtime is published as a Next.js route.** The landing page's runtime uses `createCopilotRuntimeHandler` with `GET`/`POST` exports. A Vite app has no Next route, so its `agents` record is hosted in the Vue Quickstart's Node listener.

**3. The one Strands page backend can't load.** [Tool Rendering](https://docs.copilotkit.ai/vue/strands/generative-ui/tool-rendering) and [Sub-agents](https://docs.copilotkit.ai/vue/strands/multi-agent/subagents) print `src/agents/agent.py`: an 89-line excerpt and the full 594 lines. It defines `get_weather`, the three delegation tools and many more, but imports `tools`, `tools.todos`, `agents.gen_ui_agent`, `agents.a2ui_generate` and `agents.todo_state_sync`, none published. The file is kept verbatim (`agent/src/agents/agent.py`) and not served as a whole. **Tool Rendering's `get_weather` is served (2026-11-17, at your request: "a route with tool agent, not a separate server").** `harness_app.py` compiles only that function from the file, unchanged, with the three names it uses: `json`, `tool`, and `get_weather_impl`. `get_weather_impl` comes from the unpublished `tools` module, so it is a flagged **stand-in** returning fixed sample weather (your choice). It runs as a tool agent at `/tool-rendering` on the same agent server, with the Quickstart's model and prompt. The Tool Rendering samples use `default`, which every route shares, so they get their own runtime path on the same Node server, `/api/copilotkit-tool-rendering` (`backend/runtimes/tool-rendering.ts`, your choice). Their three `App.vue` `runtime-url`s are changed and labelled, as for MCP Apps. Verified with a fake key and a local stand-in model: the model was offered `get_weather`, the tool ran, its result went back to the model, and all three renderers drew the call. Per-tool's `WeatherToolCard.vue` reads `parameters.city`, but the tool's argument is `location`, so its heading stays empty (doc bug, left as published). The delegation tools and the rest of the file stay unserved. Sub-agents' "Rendering a live delegation log" publishes no Vue code.

**4. No backend for shared state.** State Rendering, Shared State and State Streaming publish no Strands backend. Their agent ids are `my_agent`, which writes no state, so `ResearchProgress` stays "Idle", the notes list stays empty, `StreamingDocument` never fills, and the Canvas can't be edited by the agent. UI-side state (seeding, the tone write-back) still works.

**5. Interrupts: a tool, no agent.** [HITL Overview](https://docs.copilotkit.ai/vue/strands/human-in-the-loop) and [Pausing the Agent for Input](https://docs.copilotkit.ai/vue/strands/human-in-the-loop/useInterrupt) print the same `src/agents/interrupt_agent.py`: a `@tool(context=True)` `schedule_meeting` that calls `tool_context.interrupt(...)`. It has no imports (`tool`, `ToolContext`, `Mapping`) and no `Agent`. Both pages say the showcase mounts a dedicated interrupt agent for the interrupt demos' agent names, leaving `schedule_meeting` on the shared agent for the frontend-tool flow. At your request ("Imports + agent"), `agent/harness_app.py` (flagged) runs the file unchanged with those three names, builds an `Agent` from the Quickstart's model and prompt plus `tools=[schedule_meeting]`, and mounts it at `/interrupt` with `add_strands_fastapi_endpoint`. `gen-ui-interrupt` and `interrupt-headless` point there; HITL Overview's `default` stays on the Quickstart agent. `MeetingChat.vue` resolves with `chosen_label`/`chosen_time` or `cancelled`, which is what the tool reads. Verified with a fake key: both ids reach `/interrupt` and OpenAI (401). [Headless Interrupts](https://docs.copilotkit.ai/vue/strands/human-in-the-loop/headless) publishes no backend; its Start button sends "Prepare the governed action.", which the meeting tool doesn't fit, so no interrupt is expected there. `lookupUserDepartment` in the `handler` sample is undefined.

**6. Undefined functions left undefined.** `searchOrders` (WebMCP: as published every call throws; the demo shows only a flagged stand-in sample, your choice), `executeSideEffect` (Governed Actions), `lookupUserDepartment` (useInterrupt), and on the Components pages `useCartStore` (`./cart-store`) and `vueBasicCatalog`.

**7. Threads: Intelligence quickstart runtime.** Wired per the [Vue Strands Intelligence quickstart](https://docs.copilotkit.ai/vue/strands/intelligence/quickstart). Its `authenticateApplicationUser` is never defined; per that page's "a fixed identity is suitable only for a local, single-user demo", it returns `local-user` / "Local user" (flagged, **not authentication**). Without `CPK_INTELLIGENCE_API_KEY` the path is plain SSE, and the runtime logs that `GET /threads` returns 403. Restart the backend after `project select`. The Threads `App.vue` files use `/api/copilotkit-threads` (published value kept as a comment).

**8. MCP Apps.** The published server URL is a placeholder, replaced by the page's own `http://localhost:3101/mcp` example served by `npm run mcp:apps`. It runs on its own runtime path because `mcpApps` applies to every agent on a runtime; both `App.vue` `runtime-url`s are changed (labelled).

**9. Type errors in published doc code** (`npm run type-check`, 9 errors): the `labels` prop is typed as literal default strings; `useRenderTool`, `useDefaultRenderTool` and `useHumanInTheLoop` reject render components that declare only the props they use; `searchOrders` ×2; Surfaces' `FeaturedProducts.vue` imports `../product`, a type module no page publishes. `npm run build` is `vite build`.

**10. Slots › Disclaimer never renders.** `CopilotChat`'s `#input` slot props don't include `showDisclaimer`, so the sample's `CopilotChatInput` never shows its `#disclaimer` slot. Left as published.

**11. Fragments, stand-ins and wrappers.** Slots' fragments get imports only, and "Three levels" is nested in "Two levels". Headless UI's `RenderedMessages.vue` is mounted with the minimal `HeadlessChat.vue` as its composer. Shared State's two `SharedWorkspace.vue` fragments are merged. Stand-ins: `TimePickerCard.vue`, `CustomMessageView`, `CustomToolbarAction`, `BrandedToolCard`, `searchOrders` (on request). `HarnessApp.vue` mounts HITL's `MeetingApproval` beside a chat. **Shown only:** `agent.subscribe`, Programmatic Control's resume fragment, the watch-sources line, Headless Threads' pagination, `toggleItem`, useInterrupt's `enabled`/`handler`/multi-interrupt samples, and Governed Actions' type and `handleApproval`.

**12. Port 8000.** The Quickstart's `main.py` (and `harness_app.py`, which mirrors it) hard-codes port 8000 (`uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)`). If something else already listens there, the runtime reaches that server instead and runs fail with `HTTP 404`. Use the `uvicorn harness_app:app --port …` alternative in §6.

**13. The harness itself.** There's no root `CopilotKitProvider`: each demo mounts its page's own `App.vue`. Doc sync runs as Vite dev-server middleware and diffs the `.md` of all 31 tracked pages (the 22 Vue pages and the nine Components pages), so changes to the landing runtime block or the Strands Quickstart are invisible to it. `npm run doc-files` re-reads both live.

**14. Catalog parsing bug, found and fixed (2026-11-13).** The block-catalog builder first recognised only backtick fences. HITL Overview and useInterrupt print `interrupt_agent.py` in a **tilde** fence (`~~~~python`), so it was invisible and the interrupt pages briefly looked like they had no backend. The builder now reads both fence styles, as well as code the rendered page carries in RSC text chunks. Every generated file was regenerated and verified byte-identical, and the newly visible block is applied above (§3, §9.5).

**16. `reasoning_effort` fix on the Quickstart model (added 2026-11-17, at your request).** As published, the [Strands Quickstart](https://docs.copilotkit.ai/strands/quickstart?agent=bring-your-own)'s `OpenAIModel(model_id="gpt-6-luna")` passes no `params`, and Strands calls `/v1/chat/completions`. A plain chat works, but any run that carries a tool (`render_ui` from a catalog, frontend tools, `get_weather`, `schedule_meeting`) fails with `RUN_ERROR` `400 - Function tools with reasoning_effort are not supported for gpt-6-luna in /v1/chat/completions … set reasoning_effort to 'none'` (`STRANDS_FORCE_STOP`). Neither Strands nor `ag-ui-strands` sets `reasoning_effort`, so the model's own default triggers the error. The docs already pass `reasoning_effort="none"` on their direct gpt-6-luna call in Sub-agents' `agent.py`, but the Quickstart doesn't. **Fix (flagged):** a single added line, `params={"reasoning_effort": "none"}`, in `agent/main.py`. `write-doc-files.py` applies it, so `npm run doc-files` puts it back, and asserts the published model block hasn't changed. The same line is in `harness_app.py`'s `/interrupt` and `/tool-rendering` models. **Doc bug:** the Quickstart agent fails as soon as a reader adds a tool.

**15. Generative UI › Components (added 2026-11-17).**
- **The pages.** The nine pages live under `/strands/generative-ui/components`, not `/vue`, and print each sample in React, Angular, React Native and Vue tabs. Only the Vue tab and untabbed code are used; tab membership is read from the snapshot's `<Tab value="Vue">` markup.
- **The agent (the ms-agent-py choice, same rules).** The overview's Vue setup includes its own runtime: a TanStack `BuiltInAgent` (`@tanstack/ai`, `openaiText("gpt-6-luna")`, `convertInputToTanStackAI`). It's shown on the route and not served. The samples keep `runtime-url="/api/copilotkit"`, so they run on the Strands Quickstart agent.
- **The guide reaches the model.** For a run that carries a catalog, the Copilot Runtime's generative-UI middleware adds `render_ui` to the run's tools and its guide (components, props, how to call the tool) to the run's context (`@copilotkit/runtime` 1.87.0, `generative-ui-middleware`). `ag-ui-strands` registers `render_ui` as a proxy tool and puts the context at the top of the user message ("Context provided by the application:"). Its A2UI-specific filters drop only the `@ag-ui/a2ui-middleware` schema and `render_a2ui` guides, not this one, and the harness runtime requests no A2UI injection. **Captured 2026-11-17** with a fake key and a local stand-in for OpenAI: Catalogs sent `tools: [render_ui]` with the guide; Transports › markdown and Markdown mode sent the markdown guide; `sendContext: false` sent neither. Not yet checked against a live model.
- **What the harness wrote, all flagged:**
  - Five pages print only an opening `<CopilotKitProvider …>` line (Catalogs, Transports ×3, Markdown mode's `sendContext: false`, Adopt from A2UI's "After"). The harness adds the imports, a `<CopilotChat />` and the closing tag.
  - Three pages print a provider component with a `<slot />` (Standard catalog, Theming, Markdown mode's `App.vue`). The harness puts a `<CopilotChat />` in the slot.
  - Surfaces, Standard catalog's override and State and actions get small harness pages that put the published pieces together.
  - Two modules printed without imports (State and actions' `shop-ui.ts`, Adopt from A2UI's `app-ui.ts`) get only their import lines.
  - Surfaces' `FeaturedProducts.vue` imports `../shop-ui`, which that page never prints. The Catalogs page's `shop-ui.ts` (same `acme/shop@1`) and its two components are copied there, labelled.
  - The overview's plugin entry (`GenerativeUIChart`, `GenerativeUIMap`) is applied in the harness's `src/main.ts`, and `chart.js` and `maplibre-gl` are installed as the page says.
- **Stand-ins (flagged):** `ProductRow` (Surfaces), `Airport` and `Arrow` (Adopt from A2UI).
- **Shown only:**
  - Catalogs' type-error demo and its `exportA2UICatalog` script;
  - Surfaces' recommendations sample (`Product` type never published);
  - State and actions' cart samples (`./cart-store` never published);
  - Theming's `index.html` dark-mode script, since it would affect every route;
  - Markdown mode's backend fragment (`MY_PROMPT` undefined);
  - Adopt from A2UI's "Before" (`vueBasicCatalog` undefined).

---

## 10. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Connection refused, or `RUN_ERROR` naming the agent URL | Agent not running, or `AGENT_URL` unset | Start terminal 1; set `AGENT_URL` in `backend/.env`; restart the backend. |
| `RUN_ERROR "HTTP 404"` | Another server holds port 8000 | §6: run on another port and update `AGENT_URL`. |
| Runtime logs `Agent execution failed: [TypeError: fetch failed]` … `ECONNREFUSED 127.0.0.1:8001` | `AGENT_URL` and the agent's port don't match. `backend/.env` points at `http://localhost:8001/`, but `uv run harness_app.py` (and `main.py`) always listens on **8000**, so nothing answers on 8001. The startup line `Agent: http://localhost:8001/` shows which URL the runtime uses. | Use the same port in both places, either way: set `AGENT_URL=http://localhost:8000/` in `backend/.env`, **or** start the agent on 8001 with `cd agent && uv run --env-file .env uvicorn harness_app:app --port 8001`. Then restart `npm run dev`, because `tsx watch` doesn't reload `.env`. Check the port with `ss -ltnp \| grep 800`. |
| `RUN_ERROR "Error code: 401 - Incorrect API key"` | `OPENAI_API_KEY` missing or wrong in **`agent/.env`** | Fix it and restart the agent with `--env-file .env`. |
| `Agent … not found` | Backend isn't this repo's `server.ts` | Run `backend/server.ts`. |
| Threads stay on "Loading threads…" | Runtime started before the key existed (SSE → 403) | Restart the backend; the startup line must say `(intelligence)`. |
| CORS error on `/quickstart` or `/generative-ui/components` | Those `App.vue` files call `:8200` directly | Keep `cors: true`. |
| `Port 5173 is in use` | Another harness's Vite | Stop it (one harness at a time on 5173/8200). |

---

## Doc drift detection

`/doc-sync` fetches the `.md` behind all 31 tracked pages, diffs each against `doc-snapshot/pages/`, replaces the snapshot, and ranks changes High/Medium/Low. Commit `pages/`, `manifest.json` and `CHANGELOG.md`; `reports/` is gitignored. **Regenerating the doc files:** `cd frontend && npm run doc-files` rebuilds the block catalog (snapshot pages, plus the Strands Quickstart fetched live, every block checked against the rendered page). It then rewrites the verbatim doc files (`write-genui-files.py` writes the Components routes' files), `src/lib/published.json`, `agent/main.py`, `agent/src/agents/agent.py` and `agent/src/agents/interrupt_agent.py`.

---

## 11. Project structure

```
aws-strands-py/
├── CLAUDE.md · PR_GUIDELINES.md · README.md · .env.example
├── doc-snapshot/                    # pages/*.md + manifest.json — doc-sync baseline
├── agent/                           # Strands (Python, uv) — FastAPI :8000
│   ├── main.py                      # ★ Strands Quickstart agent, verbatim + 1 flagged line (§9.16)
│   ├── harness_app.py               # [harness, flagged] serves main.app + /interrupt (§9.5) + /tool-rendering (§9.3)
│   └── src/agents/
│       ├── interrupt_agent.py       # HITL / useInterrupt tool, verbatim — served via harness_app.py
│       └── agent.py                 # Vue pages' backend, verbatim; only get_weather is served (§9.3)
├── backend/                         # Copilot Runtime, Node :8200
│   ├── server.ts                    # ★ Vue Quickstart host + landing runtime
│   ├── agents.ts                    # HttpAgent per doc agent id
│   └── runtimes/ threads.ts · mcp-apps.ts · tool-rendering.ts
└── frontend/                        # Vite + Vue 3
    ├── scripts/ build-doc-catalog.py · write-doc-files.py · write-genui-files.py · write-demo-entries.py
    └── src/ lib/nav-config.ts (★ routes + statuses) · routes/<doc path>/{Notes.vue, demo-chat/} · …
```

---

## 12. References

**Getting Started**: [Quickstart (landing)](https://docs.copilotkit.ai/vue/strands) · [Vue Quickstart (frontend steps)](https://docs.copilotkit.ai/vue) · [Strands Quickstart (agent)](https://docs.copilotkit.ai/strands/quickstart)

**Basics**: [Prebuilt Components](https://docs.copilotkit.ai/vue/strands/prebuilt-components) · [Slots](https://docs.copilotkit.ai/vue/strands/custom-look-and-feel/slots) · [Headless UI](https://docs.copilotkit.ai/vue/strands/custom-look-and-feel/headless-ui) · [Programmatic Control](https://docs.copilotkit.ai/vue/strands/programmatic-control) · [Threads Drawer](https://docs.copilotkit.ai/vue/strands/prebuilt-components/copilot-threads-drawer) · [Headless Threads](https://docs.copilotkit.ai/vue/strands/headless-threads) · [Frontend Tools](https://docs.copilotkit.ai/vue/strands/frontend-tools)

**Generative UI**: [Components as Tools](https://docs.copilotkit.ai/vue/strands/generative-ui/tool-based) · [Tool Call Rendering](https://docs.copilotkit.ai/vue/strands/generative-ui/tool-rendering) · [State Rendering](https://docs.copilotkit.ai/vue/strands/generative-ui/state-rendering) · [MCP Apps](https://docs.copilotkit.ai/vue/strands/generative-ui/mcp-apps)

**Generative UI › Components**: [Components and surfaces](https://docs.copilotkit.ai/strands/generative-ui/components) · [Surfaces](https://docs.copilotkit.ai/strands/generative-ui/components/surfaces) · [Catalogs](https://docs.copilotkit.ai/strands/generative-ui/components/catalogs) · [Standard catalog](https://docs.copilotkit.ai/strands/generative-ui/components/standard-catalog) · [State and actions](https://docs.copilotkit.ai/strands/generative-ui/components/state-and-actions) · [Theming](https://docs.copilotkit.ai/strands/generative-ui/components/theming) · [Transports](https://docs.copilotkit.ai/strands/generative-ui/components/transports) · [Markdown mode](https://docs.copilotkit.ai/strands/generative-ui/components/markdown-mode) · [Adopt from A2UI](https://docs.copilotkit.ai/strands/generative-ui/components/from-a2ui)

**Interactivity**: [Shared State](https://docs.copilotkit.ai/vue/strands/shared-state) · [Render agent state in your app](https://docs.copilotkit.ai/vue/strands/shared-state/rendering-in-app) · [State Streaming](https://docs.copilotkit.ai/vue/strands/shared-state/streaming) · [Agent Read-Only Context](https://docs.copilotkit.ai/vue/strands/shared-state/agent-readonly) · [HITL Overview](https://docs.copilotkit.ai/vue/strands/human-in-the-loop) · [Pausing the Agent for Input](https://docs.copilotkit.ai/vue/strands/human-in-the-loop/useInterrupt) · [Headless Interrupts](https://docs.copilotkit.ai/vue/strands/human-in-the-loop/headless) · [Governed Action Approval UI](https://docs.copilotkit.ai/vue/strands/human-in-the-loop/governed-actions) · [WebMCP](https://docs.copilotkit.ai/vue/strands/webmcp)

**Agent capabilities**: [Sub-agents](https://docs.copilotkit.ai/vue/strands/multi-agent/subagents)

**Intelligence (Threads routes)**: [Connect Intelligence in 5 minutes](https://docs.copilotkit.ai/vue/strands/intelligence/quickstart)

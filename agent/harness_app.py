"""
[harness] NOT FROM THE DOCS — the app this repo serves (`uv run --env-file .env
harness_app.py`). It is the Strands Quickstart's `app` (main.py, verbatim and
unchanged) plus one more endpoint, added at the user's request ("Imports +
agent (flagged)"):

- HITL Overview and useInterrupt publish src/agents/interrupt_agent.py: the
  `schedule_meeting` tool only, with no imports and no Agent. Both pages say
  the showcase "mounts a dedicated interrupt agent and points the interrupt
  demos' agent names at it". The file is kept verbatim; this module runs its
  source with the three names it uses but never imports (`tool`,
  `ToolContext`, `Mapping`), then builds an Agent from the Quickstart's own
  OpenAIModel and system prompt, adding only `tools=[schedule_meeting]`, and
  mounts it at /interrupt with ag_ui_strands' add_strands_fastapi_endpoint.

- Tool Rendering (and Sub-agents) publish src/agents/agent.py, whose
  `get_weather` tool is what the page renders. The file can't be imported (it
  imports five unpublished modules), so this module compiles only the
  `get_weather` function from it, unchanged, with the names it uses: `json`,
  `tool`, and `get_weather_impl`. `get_weather_impl` lives in the unpublished
  `tools` module, so it is a STAND-IN below (user's choice) returning fixed
  sample weather. The tool agent (Quickstart model and prompt + get_weather)
  is mounted at /tool-rendering on this same app (user's choice: a route,
  not a separate server).

The `__main__` block mirrors the Quickstart's (0.0.0.0:8000).

Both models carry main.py's one flagged addition, params={"reasoning_effort": "none"}:
without it gpt-6-luna rejects function tools on Chat Completions (README §9.16).
"""
import ast
import json
import os
from collections.abc import Mapping
from pathlib import Path

from ag_ui_strands import StrandsAgent, add_strands_fastapi_endpoint
from strands import Agent, ToolContext, tool
from strands.models.openai import OpenAIModel

from main import app

# [harness] The imports the published file omits — supplied, not edited in.
_published = Path(__file__).parent / "src" / "agents" / "interrupt_agent.py"
_namespace = {"tool": tool, "ToolContext": ToolContext, "Mapping": Mapping}
exec(compile(_published.read_text(), str(_published), "exec"), _namespace)
schedule_meeting = _namespace["schedule_meeting"]

# [harness] The Quickstart's model and prompt (main.py), plus the page's tool.
interrupt_agent = Agent(
    model=OpenAIModel(
        client_args={"api_key": os.getenv("OPENAI_API_KEY", "")},
        model_id="gpt-6-luna",
        params={"reasoning_effort": "none"},  # [harness] same fix as main.py (README §9.16)
    ),
    system_prompt="You are a helpful AI assistant.",
    tools=[schedule_meeting],
)

add_strands_fastapi_endpoint(
    app,
    StrandsAgent(agent=interrupt_agent, name="strands_agent"),
    "/interrupt",
)


# ── [harness] Tool Rendering: the published get_weather on /tool-rendering ──
def get_weather_impl(location: str) -> dict:
    """[harness] STAND-IN — NOT FROM THE DOCS. The page's get_weather calls
    get_weather_impl from the `tools` module, which no page publishes. Fixed
    sample data, no network, so the rendered card has a result to show."""
    return {
        "location": location,
        "temperature": 22,
        "conditions": "Sunny",
        "humidity": 40,
        "note": "harness stand-in data",
    }


def _published_function(path: Path, name: str, namespace: dict):
    """Compile one top-level function from a published file, unchanged."""
    tree = ast.parse(path.read_text(), str(path))
    (node,) = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name]
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), namespace)
    return namespace[name]


get_weather = _published_function(
    Path(__file__).parent / "src" / "agents" / "agent.py",
    "get_weather",
    {"json": json, "tool": tool, "get_weather_impl": get_weather_impl},
)

tool_rendering_agent = Agent(
    model=OpenAIModel(
        client_args={"api_key": os.getenv("OPENAI_API_KEY", "")},
        model_id="gpt-6-luna",
        params={"reasoning_effort": "none"},  # [harness] same fix as main.py (README §9.16)
    ),
    system_prompt="You are a helpful AI assistant.",
    tools=[get_weather],
)

add_strands_fastapi_endpoint(
    app,
    StrandsAgent(agent=tool_rendering_agent, name="strands_agent"),
    "/tool-rendering",
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

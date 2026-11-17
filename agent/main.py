import os

from ag_ui_strands import StrandsAgent, create_strands_app
from strands import Agent
from strands.models.openai import OpenAIModel

# Setup your Strands agent
api_key = os.getenv("OPENAI_API_KEY", "")
model = OpenAIModel(
    client_args={"api_key": api_key},
    model_id="gpt-6-luna",
    params={"reasoning_effort": "none"},  # [harness] not in the docs: gpt-6-luna rejects function tools on Chat Completions otherwise (README §9.16)
)

agent = Agent(
    model=model,
    system_prompt="You are a helpful AI assistant.",
)

# Wrap with AG-UI integration
agui_agent = StrandsAgent(
    agent=agent,
    name="strands_agent",
)

# Create the FastAPI app
app = create_strands_app(agui_agent, "/")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

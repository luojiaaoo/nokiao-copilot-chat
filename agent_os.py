from agno.agent.agent import Agent
from agno.models.siliconflow import Siliconflow
from agno.os import AgentOS
from agno.os.interfaces.agui import AGUI
from agno.os.interfaces.agui.router import run_agent as agui_run_agent
from ag_ui.core import RunAgentInput
from ag_ui.encoder import EventEncoder
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import json

chat_agent = Agent(
    name="Assistant",
    model=Siliconflow(
        id="Pro/MiniMaxAI/MiniMax-M2.5",
        api_key="sk-vjgpmpjndtvhkxxxxxbqrudhydhiesles",
        base_url="https://api.siliconflow.cn/v1",
    ),
    instructions="You are a helpful AI assistant.",
    add_datetime_to_context=True,
    markdown=True,
)

agent_os = AgentOS(
    agents=[chat_agent],
    interfaces=[AGUI(agent=chat_agent)],
)
app = agent_os.get_app()


@app.middleware("http")
async def agui_info_compat_middleware(request: Request, call_next):
    # CopilotKit AG-UI client may probe the runtime with: {"method":"info"}.
    # Agno's /agui endpoint validates against RunAgentInput directly, so we short-circuit it.
    if request.method == "POST" and request.url.path.rstrip("/") == "/agui":
        raw = await request.body()
        if raw:
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = None
            if isinstance(payload, dict) and payload.get("method") == "info":
                return JSONResponse(
                    {
                        "version": "1.0.0",
                        "audioFileTranscriptionEnabled": False,
                        "agents": {
                            "default": {
                                "name": chat_agent.name or "Assistant",
                                "className": "agno-agent",
                                "description": "Default AGUI agent exposed for CopilotKit runtimeUrl",
                            }
                        },
                    }
                )

            # CopilotKit may send RPC envelope:
            # {"method":"agent/run","params":{"agentId":"default"},"body":{...RunAgentInput...}}
            # Agno expects RunAgentInput fields at the top level body.
            if isinstance(payload, dict) and payload.get("method") == "agent/run":
                run_body = payload.get("body")
                if isinstance(run_body, dict):
                    try:
                        if hasattr(RunAgentInput, "model_validate"):
                            run_input = RunAgentInput.model_validate(run_body)  # type: ignore[attr-defined]
                        else:
                            run_input = RunAgentInput(**run_body)
                    except Exception as e:
                        return JSONResponse(
                            {"detail": f"Invalid agent/run payload: {e}"},
                            status_code=422,
                        )

                    encoder = EventEncoder()

                    async def event_generator():
                        async for event in agui_run_agent(chat_agent, run_input):
                            yield encoder.encode(event)

                    return StreamingResponse(
                        event_generator(),
                        media_type="text/event-stream",
                        headers={
                            "Cache-Control": "no-cache",
                            "Connection": "keep-alive",
                            "Access-Control-Allow-Origin": "*",
                            "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
                            "Access-Control-Allow-Headers": "*",
                        },
                    )

    return await call_next(request)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8050",
        "http://127.0.0.1:8050",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    agent_os.serve(app="agent_os:app", port=8000, reload=True)

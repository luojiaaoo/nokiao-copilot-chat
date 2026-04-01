from agno.os import AgentOS
from agno.os.interfaces.agui import AGUI
from fastapi.middleware.cors import CORSMiddleware
from agno.agent.agent import Agent
from agno.models.siliconflow import Siliconflow

chat_agent = Agent(
    name="Assistant",
    model=Siliconflow(
        id="Pro/MiniMaxAI/MiniMax-M2.5",
        api_key="sk-vnotauwtuxlymyzczpyoxxxsphsvyjmeumcgupkegwxz",
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

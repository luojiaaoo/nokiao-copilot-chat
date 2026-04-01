from __future__ import annotations
from agno.agent.agent import Agent
from agno.models.siliconflow import Siliconflow
from agno.os import AgentOS
from agno.os.interfaces.agui import AGUI
from multiprocessing import freeze_support
import dash
from dash import html, Input, Output, State

import nokiao_copilot_chat as ncc

dash_app = dash.Dash(
    __name__,
    backend="fastapi",
)

dash_app.layout = html.Div(
    [
        ncc.NokiaoCopilotChat(
            id="copilot-chat",
            agent="Assistant",
            agui_url="/agui",
            headers={"Authorization": "Bearer <YOUR_TOKEN>"},
            labels={
                "initial": "Hi, how can I help you today?",
                "placeholder": "Ask anything...",
            },
            style={"maxWidth": "920px", "margin": "24px auto", "height": "600px"},
        ),
        html.Pre(id="chat-state", style={"whiteSpace": "pre-wrap"}),
    ]
)


@dash.callback(
    Output("chat-state", "children"),
    Input("copilot-chat", "event_seq"),
    [
        State("copilot-chat", "thread_id"),
        State("copilot-chat", "last_user_message"),
        State("copilot-chat", "last_assistant_message"),
        State("copilot-chat", "is_running"),
    ],
)
def show_bridge_state(_, thread_id, last_user, last_assistant, is_running):
    return (
        f"thread_id: {thread_id}\n"
        f"is_running: {is_running}\n"
        f"last_user_message: {last_user}\n"
        f"last_assistant_message: {last_assistant}"
    )


chat_agent = Agent(
    name="Assistant",
    model=Siliconflow(
        id="Pro/MiniMaxAI/MiniMax-M2.5",
        api_key="sk-vnotauwtuxxxxxsinsphsvyjmeumcgupkegwxz",
        base_url="https://api.siliconflow.cn/v1",
    ),
    instructions="You are a helpful AI assistant.",
    add_datetime_to_context=True,
    markdown=True,
)

agent_os = AgentOS(
    agents=[chat_agent],
    interfaces=[AGUI(agent=chat_agent)],
    base_app=dash_app.server,
    on_route_conflict="preserve_agentos",
)

fastapi_app = agent_os.get_app()

if __name__ == "__main__":
    freeze_support()
    agent_os.serve(app="agno_dash:fastapi_app", reload=True)

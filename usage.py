import nokiao_copilot_chat as ncc
import dash
from dash import html, Input, Output

app = dash.Dash()

app.layout = html.Div(
    [
        ncc.NokiaoCopilotChat(
            id="copilot-chat",
            agent="Assistant",
            agui_url="http://localhost:8000/agui",
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


@app.callback(
    Output("chat-state", "children"),
    Input("copilot-chat", "event_seq"),
    Input("copilot-chat", "thread_id"),
    Input("copilot-chat", "last_user_message"),
    Input("copilot-chat", "last_assistant_message"),
    Input("copilot-chat", "is_running"),
)
def show_bridge_state(_, thread_id, last_user, last_assistant, is_running):
    return (
        f"thread_id: {thread_id}\n"
        f"is_running: {is_running}\n"
        f"last_user_message: {last_user}\n"
        f"last_assistant_message: {last_assistant}"
    )


if __name__ == '__main__':
    app.run(debug=True)

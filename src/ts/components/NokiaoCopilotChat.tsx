import React, {useEffect, useMemo, useRef} from "react";
import {CopilotKit, useCopilotChat, useCopilotContext} from "@copilotkit/react-core";
import {CopilotChat, Markdown, useChatContext} from "@copilotkit/react-ui";
import {HttpAgent} from "@ag-ui/client";
import {DashComponentProps} from "../props";
import "@copilotkit/react-ui/styles.css";

type ChatMessage = {
  role?: string;
  content?: unknown;
  text?: string;
  parts?: Array<{text?: string; content?: string}>;
  type?: string;
};

type AssistantMessagePropsLite = {
  message?: {content?: string; generativeUI?: () => React.ReactNode; generativeUIPosition?: string};
  isLoading: boolean;
  isCurrentMessage?: boolean;
  onRegenerate?: () => void;
  onCopy?: (message: string) => void;
  markdownTagRenderers?: Record<string, React.FC<any>>;
  subComponent?: React.ReactNode;
};

type BridgePayload = {
  thread_id?: string;
  last_user_message?: string;
  last_assistant_message?: string;
  is_running: boolean;
};

type Props = {
  /** Dash component id. */
  id?: string;
  /** Direct AG-UI endpoint URL (for example `http://localhost:8000/agui`) for pure frontend mode. */
  agui_url?: string;
  /** Extra request headers, for example Authorization. */
  headers?: Record<string, string>;
  /** Optional agent name. */
  agent?: string;
  /** Input placeholder (mapped to labels.placeholder). */
  placeholder?: string;
  /** Custom chat labels passed to CopilotChat. */
  labels?: {
    initial?: string | string[];
    placeholder?: string;
    error?: string;
    stopGenerating?: string;
    regenerateResponse?: string;
    copyToClipboard?: string;
    thumbsUp?: string;
    thumbsDown?: string;
    copied?: string;
  };
  /** Custom class name for CopilotChat root. */
  class_name?: string;
  /** Container inline style. */
  style?: Record<string, unknown>;
  /** Current thread id (input/output). */
  thread_id?: string;
  /** Latest user message text (output). */
  last_user_message?: string;
  /** Latest assistant message text (output). */
  last_assistant_message?: string;
  /** Whether generation is running (output). */
  is_running?: boolean;
  /** Incrementing sequence to trigger Dash callbacks (output). */
  event_seq?: number;
  /** Whether to show thumbs up/down feedback buttons. Default: false. */
  show_feedback_buttons?: boolean;
} & DashComponentProps;

const AssistantMessageNoFeedback = (props: AssistantMessagePropsLite) => {
  const {icons, labels} = useChatContext();
  const {message, isLoading, onRegenerate, onCopy, isCurrentMessage, markdownTagRenderers} = props;
  const [copied, setCopied] = React.useState(false);

  const content = message?.content || "";
  const subComponent = message?.generativeUI?.() ?? props.subComponent;
  const subComponentPosition = message?.generativeUIPosition ?? "after";
  const renderBefore = subComponent && subComponentPosition === "before";
  const renderAfter = subComponent && subComponentPosition !== "before";

  return (
    <>
      {renderBefore ? <div style={{marginBottom: "0.5rem"}}>{subComponent}</div> : null}
      {content ? (
        <div className="copilotKitMessage copilotKitAssistantMessage">
          <Markdown content={content} components={markdownTagRenderers as never} />
          {!isLoading ? (
            <div
              className={`copilotKitMessageControls ${isCurrentMessage ? "currentMessage" : ""}`}
            >
              <button
                className="copilotKitMessageControlButton"
                onClick={() => onRegenerate?.()}
                aria-label={labels.regenerateResponse}
                title={labels.regenerateResponse}
              >
                {icons.regenerateIcon}
              </button>
              <button
                className="copilotKitMessageControlButton"
                onClick={() => {
                  if (!content) {
                    return;
                  }
                  navigator.clipboard.writeText(content);
                  setCopied(true);
                  onCopy?.(content);
                  setTimeout(() => setCopied(false), 2000);
                }}
                aria-label={labels.copyToClipboard}
                title={labels.copyToClipboard}
              >
                {copied ? <span style={{fontSize: "10px", fontWeight: "bold"}}>OK</span> : icons.copyIcon}
              </button>
            </div>
          ) : null}
        </div>
      ) : null}
      {renderAfter ? <div style={{marginBottom: "0.5rem"}}>{subComponent}</div> : null}
      {isLoading ? <span>{icons.activityIcon}</span> : null}
    </>
  );
};

function toText(content: unknown): string {
  if (typeof content === "string") {
    return content;
  }
  if (Array.isArray(content)) {
    return content
      .map((item) => {
        if (typeof item === "string") {
          return item;
        }
        if (item && typeof item === "object") {
          const obj = item as Record<string, unknown>;
          if (typeof obj.text === "string") {
            return obj.text;
          }
          if (typeof obj.content === "string") {
            return obj.content;
          }
        }
        return "";
      })
      .filter(Boolean)
      .join("\n");
  }
  if (content && typeof content === "object") {
    const obj = content as Record<string, unknown>;
    if (typeof obj.text === "string") {
      return obj.text;
    }
  }
  return "";
}

function extractMessageText(message: ChatMessage): string {
  if (typeof message.text === "string") {
    return message.text;
  }
  if (typeof message.content === "string") {
    return message.content;
  }
  if (Array.isArray(message.parts)) {
    return message.parts
      .map((part) => part.text || part.content || "")
      .filter(Boolean)
      .join("\n");
  }
  return toText(message.content);
}

function computeLastMessages(messages: unknown): {
  last_user_message?: string;
  last_assistant_message?: string;
} {
  if (!Array.isArray(messages)) {
    return {};
  }

  let lastUser = "";
  let lastAssistant = "";
  for (const item of messages) {
    if (!item || typeof item !== "object") {
      continue;
    }
    const message = item as ChatMessage;
    const role = (message.role || message.type || "").toLowerCase();
    const text = extractMessageText(message).trim();
    if (!text) {
      continue;
    }
    if (role.includes("user")) {
      lastUser = text;
    } else if (role.includes("assistant")) {
      lastAssistant = text;
    }
  }

  return {
    last_user_message: lastUser || undefined,
    last_assistant_message: lastAssistant || undefined,
  };
}

function BridgeObserver(props: {
  setProps: DashComponentProps["setProps"];
  defaults: {
    thread_id?: string;
    last_user_message?: string;
    last_assistant_message?: string;
    is_running?: boolean;
  };
}) {
  const {setProps, defaults} = props;
  const {visibleMessages, isLoading} = useCopilotChat();
  const {threadId} = useCopilotContext();
  const eventSeqRef = useRef(0);
  const lastSentRef = useRef("");

  useEffect(() => {
    const lastMessages = computeLastMessages(visibleMessages);
    const payload: BridgePayload = {
      thread_id: threadId || defaults.thread_id,
      last_user_message: lastMessages.last_user_message || defaults.last_user_message,
      last_assistant_message:
        lastMessages.last_assistant_message || defaults.last_assistant_message,
      is_running: isLoading ?? defaults.is_running ?? false,
    };

    const signature = JSON.stringify(payload);
    if (signature === lastSentRef.current) {
      return;
    }

    lastSentRef.current = signature;
    eventSeqRef.current += 1;
    setProps({
      ...payload,
      event_seq: eventSeqRef.current,
    });
  }, [
    defaults.is_running,
    defaults.last_assistant_message,
    defaults.last_user_message,
    defaults.thread_id,
    isLoading,
    setProps,
    threadId,
    visibleMessages,
  ]);

  return null;
}

/** Dash Copilot chat component backed by CopilotKit runtimeUrl (Agno AGUI compatible). */
const NokiaoCopilotChat = (props: Props) => {
  const {
    id,
    agui_url,
    headers,
    agent,
    placeholder,
    labels,
    class_name,
    style,
    setProps,
    thread_id,
    last_user_message,
    last_assistant_message,
    is_running,
    show_feedback_buttons,
  } = props;

  const localAgents = useMemo(() => {
    if (!agui_url) {
      return undefined;
    }
    const agentId = agent || "default";
    return {
      [agentId]: new HttpAgent({
        url: agui_url,
      }),
    };
  }, [agui_url, agent]);

  const mergedLabels = useMemo(() => {
    return {
      ...(labels || {}),
      ...(placeholder ? {placeholder} : {}),
    };
  }, [labels, placeholder]);

  return (
    <div id={id} style={style as React.CSSProperties}>
      <CopilotKit
        runtimeUrl={agui_url}
        headers={headers}
        agent={agent}
        threadId={thread_id}
        agents__unsafe_dev_only={localAgents}
        useSingleEndpoint={false}
        showDevConsole={false}
        enableInspector={false}
      >
        <BridgeObserver
          setProps={setProps}
          defaults={{
            thread_id,
            last_user_message,
            last_assistant_message,
            is_running,
          }}
        />
        <CopilotChat
          className={class_name}
          labels={mergedLabels}
          AssistantMessage={show_feedback_buttons ? undefined : AssistantMessageNoFeedback}
        />
      </CopilotKit>
    </div>
  );
};

export default NokiaoCopilotChat;

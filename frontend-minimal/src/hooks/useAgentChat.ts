import { useEffect, useMemo, useRef, useState } from "react";

import { isAgentEndpointEnabled } from "../adapters/agentResponseAdapter";
import type {
  AgentCapabilityManifest,
  ChatResponse,
  ConversationMessage,
  DemoUser,
  ReasoningView,
} from "../types/api";

// 第 02 课精简版：只保留 加载能力 + 用户切换 + 发消息。
// resume/eval/feedback/trace/createUser 在后续课程按需加回。

const AGENT_BASE_URL = import.meta.env.VITE_AGENT_BASE_URL ?? "http://localhost:8000";

const DEFAULT_AGENT_CAPABILITIES: AgentCapabilityManifest = {
  schema_version: "agent_capabilities_v1",
  lesson: {
    id: "default-agent",
    title: "默认 Agent",
    summary: "目标 Agent 未提供能力声明时，调试后台只保留最小聊天入口。",
  },
  agent: {
    name: "小哲电商客服 Agent",
    version: "default",
  },
  endpoints: {
    health: true,
    chat: true,
    chat_resume: false,
    trace: false,
    eval_run: false,
  },
  features: {
    chat: true,
    runtime_context: false,
    reasoning_summary: false,
    reasoning_content: false,
    structured_intent: false,
    rag_citations: false,
    tool_calls: false,
    workflow: false,
    human_approval: false,
    memory: false,
    hooks: false,
    trace: false,
    evaluation: false,
    cost_summary: false,
  },
};

const welcomeMessage: ConversationMessage = {
  role: "assistant",
  content: "欢迎来到小哲电商客服 Agent 调试后台。请选择当前课程示例，或输入本课支持的问题观察响应。",
};

const initialUsers: DemoUser[] = [
  {
    profile: { userId: "U1001", nickname: "张三", memberLevel: "gold", riskLevel: "low" },
    preferences: { userId: "U1001" },
  },
  {
    profile: { userId: "U1002", nickname: "李四", memberLevel: "silver", riskLevel: "low" },
    preferences: { userId: "U1002" },
  },
  {
    profile: { userId: "U1003", nickname: "王五", memberLevel: "normal", riskLevel: "medium" },
    preferences: { userId: "U1003" },
  },
];

type ConversationState = {
  sessionId: string;
  messages: ConversationMessage[];
  activeResponse?: ChatResponse;
};

function createConversation(userId: string): ConversationState {
  return {
    sessionId: `session-${userId}-${Math.random().toString(36).slice(2, 10)}`,
    messages: [welcomeMessage],
  };
}

export function useAgentChat() {
  const [users] = useState<DemoUser[]>(initialUsers);
  const [selectedUserId, setSelectedUserId] = useState(initialUsers[0].profile.userId);
  const [conversations, setConversations] = useState<Record<string, ConversationState>>(() =>
    Object.fromEntries(
      initialUsers.map((user) => [user.profile.userId, createConversation(user.profile.userId)]),
    ),
  );
  const [isLoading, setIsLoading] = useState(false);
  const [agentCapabilities, setAgentCapabilities] = useState<AgentCapabilityManifest>(DEFAULT_AGENT_CAPABILITIES);
  const [capabilitiesError, setCapabilitiesError] = useState<string | undefined>();
  const isSendingRef = useRef(false);

  const selectedUser = useMemo(
    () => users.find((user) => user.profile.userId === selectedUserId) ?? users[0],
    [selectedUserId, users],
  );
  const activeConversation = conversations[selectedUserId] ?? createConversation(selectedUserId);

  useEffect(() => {
    let isActive = true;

    async function loadAgentCapabilities() {
      try {
        const response = await fetch(`${AGENT_BASE_URL}/capabilities`);
        if (!response.ok) {
          if (isActive) {
            setAgentCapabilities(DEFAULT_AGENT_CAPABILITIES);
            setCapabilitiesError("目标 Agent 未提供 /capabilities，调试后台只保留最小聊天入口。");
          }
          return;
        }
        const payload = (await response.json()) as AgentCapabilityManifest;
        if (isActive) {
          setAgentCapabilities(payload);
          setCapabilitiesError(undefined);
        }
      } catch {
        if (isActive) {
          setAgentCapabilities(DEFAULT_AGENT_CAPABILITIES);
          setCapabilitiesError("暂时无法读取 /capabilities，调试后台只保留最小聊天入口。");
        }
      }
    }

    void loadAgentCapabilities();

    return () => {
      isActive = false;
    };
  }, []);

  function updateActiveConversation(updater: (current: ConversationState) => ConversationState) {
    setConversations((current) => ({
      ...current,
      [selectedUserId]: updater(current[selectedUserId] ?? createConversation(selectedUserId)),
    }));
  }

  function selectUser(userId: string) {
    setSelectedUserId(userId);
    setConversations((current) =>
      current[userId] ? current : { ...current, [userId]: createConversation(userId) },
    );
  }

  async function sendMessage(userMessage: string, _reasoningView: ReasoningView) {
    if (isSendingRef.current) {
      return;
    }
    if (!isAgentEndpointEnabled(agentCapabilities, "chat")) {
      updateActiveConversation((current) => ({
        ...current,
        messages: [...current.messages, { role: "assistant", content: "当前 Agent 版本未开放 /chat。" }],
      }));
      return;
    }

    isSendingRef.current = true;
    setIsLoading(true);
    const userId = selectedUserId;
    const sessionId = activeConversation.sessionId;

    updateActiveConversation((current) => ({
      ...current,
      messages: [...current.messages, { role: "user", content: userMessage }],
    }));

    try {
      const chatResponse = await fetch(`${AGENT_BASE_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          runtime_user_id: userId,
          runtime_nickname: selectedUser.profile.nickname,
          runtime_member_level: selectedUser.profile.memberLevel,
          runtime_risk_level: selectedUser.profile.riskLevel,
          user_message: userMessage,
          history_messages: activeConversation.messages.map((message) => ({
            role: message.role,
            content: message.content,
          })),
          debug: true,
        }),
      });

      if (!chatResponse.ok) {
        const errorPayload = (await chatResponse.json().catch(() => undefined)) as { detail?: string } | undefined;
        throw new Error(formatErrorDetail(errorPayload?.detail));
      }

      const payload = (await chatResponse.json()) as ChatResponse;
      setConversations((current) => {
        const existing = current[userId] ?? createConversation(userId);
        return {
          ...current,
          [userId]: {
            ...existing,
            messages: [...existing.messages, { role: "assistant", content: payload.answer, response: payload }],
            activeResponse: payload,
          },
        };
      });
    } catch (error) {
      updateActiveConversation((current) => ({
        ...current,
        messages: [
          ...current.messages,
          { role: "assistant", content: error instanceof Error ? error.message : "Agent 请求失败" },
        ],
      }));
    } finally {
      isSendingRef.current = false;
      setIsLoading(false);
    }
  }

  return {
    users,
    selectedUser,
    selectedUserId,
    messages: activeConversation.messages,
    isLoading,
    activeResponse: activeConversation.activeResponse,
    agentBaseUrl: AGENT_BASE_URL,
    agentCapabilities,
    capabilitiesError,
    selectUser,
    sendMessage,
  };
}

function formatErrorDetail(detail: unknown) {
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }
  if (detail) {
    return JSON.stringify(detail);
  }
  return "Agent 请求失败";
}

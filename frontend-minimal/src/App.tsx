import { FormEvent, useEffect, useMemo, useState } from "react";

import { MessageList } from "./components/MessageList";
import { SampleQuestions } from "./components/SampleQuestions";
import { getLessonScenarioSet } from "./data/demoScenarios";
import { useAgentChat } from "./hooks/useAgentChat";
import type { ReasoningView } from "./types/api";

// 第 02 课精简版：去掉 TracePanel、EvaluationPanel、学习开关和新增用户表单。
// 后续课程按需加回 import 和 JSX 块即可。

export default function App() {
  const {
    users,
    selectedUser,
    selectedUserId,
    messages,
    isLoading,
    agentBaseUrl,
    agentCapabilities,
    capabilitiesError,
    selectUser,
    sendMessage,
  } = useAgentChat();

  const scenarioSet = useMemo(
    () => getLessonScenarioSet(selectedUserId, agentCapabilities.lesson?.number),
    [selectedUserId, agentCapabilities.lesson?.number],
  );
  const [draft, setDraft] = useState(scenarioSet.defaultQuestion);

  useEffect(() => {
    setDraft(scenarioSet.defaultQuestion);
  }, [scenarioSet.defaultQuestion]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (isLoading || !draft.trim()) {
      return;
    }
    await sendMessage(draft.trim(), "off" as ReasoningView);
  }

  return (
    <main className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">E-commerce Agent Debug Console</p>
          <h1>小哲电商客服 Agent 调试后台</h1>
        </div>
        <p>第 02 课最小 /chat 调试台：验证前端能接入 Agent 后端并展示回复。</p>
      </header>

      <AgentTargetBanner
        baseUrl={agentBaseUrl}
        capabilities={agentCapabilities}
        error={capabilitiesError}
      />

      <section className="panel user-panel" aria-label="调试用户">
        <div className="panel-header">
          <span>调试用户</span>
          <small>切换用户会切换聊天历史</small>
        </div>
        <div className="user-tabs">
          {users.map((user) => (
            <button
              key={user.profile.userId}
              type="button"
              className={user.profile.userId === selectedUserId ? "active" : ""}
              onClick={() => selectUser(user.profile.userId)}
            >
              <strong>{user.profile.nickname}</strong>
              <small>
                {user.profile.userId} · {user.profile.memberLevel} · risk {user.profile.riskLevel}
              </small>
            </button>
          ))}
        </div>
        <div className="user-summary">
          <strong>
            {selectedUser.profile.nickname} / {selectedUser.profile.userId}
          </strong>
        </div>
      </section>

      <section className="top-grid" aria-label="对话">
        <MessageList messages={messages} isLoading={isLoading} />
      </section>

      <section className="bottom-grid" aria-label="输入与示例">
        <form className="panel composer-panel" onSubmit={handleSubmit}>
          <div className="panel-header">
            <span>输入用户问题</span>
            <small>输入后发送给 Agent</small>
          </div>
          <textarea
            id="question"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            disabled={isLoading}
            rows={4}
            placeholder="例如：你好，我想咨询一下客服问题"
          />
          <div className="composer-actions">
            <button className="submit-button" disabled={isLoading} type="submit">
              {isLoading ? "处理中..." : "发送给 Agent"}
            </button>
          </div>
        </form>

        <SampleQuestions scenarioSet={scenarioSet} disabled={isLoading} onSelect={setDraft} />
      </section>
    </main>
  );
}

function AgentTargetBanner({
  baseUrl,
  capabilities,
  error,
}: {
  baseUrl: string;
  capabilities: { lesson?: { title?: string; id?: string }; features?: Record<string, boolean> };
  error?: string;
}) {
  const lessonTitle = capabilities.lesson?.title || "目标 Agent";
  const lessonId = capabilities.lesson?.id || "unknown";
  const enabledFeatures = Object.entries(capabilities.features ?? {}).filter(([, enabled]) => enabled).length;
  const totalFeatures = Object.keys(capabilities.features ?? {}).length;

  return (
    <section className="capability-banner" aria-label="当前 Agent 能力配置">
      <div>
        <strong>{lessonTitle}</strong>
        <span>{lessonId} · {baseUrl}</span>
      </div>
      <div className="capability-banner-meta">
        <span>{totalFeatures ? `${enabledFeatures}/${totalFeatures} 项能力开放` : "未声明能力"}</span>
        {error ? <span className="capability-warning">{error}</span> : null}
      </div>
    </section>
  );
}

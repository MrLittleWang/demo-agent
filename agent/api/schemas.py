from typing import Any, Literal

from pydantic import BaseModel, Field

# reasoning_view 仍然只是调试后台的观察开关，不代表这一版已经有隐藏推理展示。
ReasoningView = Literal["default", "off", "summary", "teaching"]
IntentSource = Literal["rules", "classifier", "rules_fallback"]
Intent = Literal[
    "general_chat",
    "promotion_consult",
    "product_consult",
    "order_query",
    "refund_request",
    "complaint",
    "unknown",
]

class ChatRequest(BaseModel):
    """调试后台发送给 `/chat` 的最小请求格式。"""
    session_id: str = Field(..., description="当前对话会话 ID")
    # runtime_* 是系统确认过的事实，不能让用户在聊天里自称会员或冒充身份。
    runtime_user_id: str = Field(..., description="调试后台当前选择的可信用户 ID")
    runtime_nickname: str | None = Field(default=None,
                                         description="调试后台当前选择的用户昵称")
    runtime_member_level: str | None = Field(default=None,
                                             description="调试后台当前选择的会员等级")
    runtime_risk_level: str | None = Field(default=None,
                                           description="调试后台当前选择的风险等级")
    # user_message 才是真正交给模型的用户输入，必须和 runtime_* 分开放。
    user_message: str = Field(..., description="用户输入的问题")
    reasoning_view: ReasoningView = "default"
    debug: bool = True
    runtime_context: dict[str, Any] | None = None


class IntentResult(BaseModel):
    """第一版系统可读意图结果。"""

    # intent 是下游系统能消费的固定枚举；不要让模型临时发明新分类。
    intent: Intent
    # source 让调试后台知道本轮来自规则、分类模型，还是安全兜底。
    source: IntentSource
    confidence: float = Field(ge=0.0, le=1.0)
    matched_keywords: list[str] = Field(default_factory=list)
    explanation: str

class ChatResponse(BaseModel):
    """从这一版开始，回答旁边多一个系统能读懂的意图标签。"""

    session_id: str
    answer: str
    intent: Intent
    intent_result: IntentResult
    reasoning_summary: list[str]
    session_state: dict[str, Any]


import httpx

from agent_logging import log_course_event, observe_chat
from api.schemas import ChatRequest, ChatResponse
from models.llm_client import call_chat_model

def build_customer_msssage(request:ChatRequest) -> list[dict[str, str]]:
    """构建客服消息列表，包含用户输入和系统事实。"""
    system_message = (
        "你是小杰电商公司的第一版 AI 客服。请用自然、耐心的客服语气回答用户问题。"
        "当前版本只接入了大模型聊天能力，还没有接入小哲电商的活动规则、订单物流、"
        "退款条件、售后流程或业务工具。"
    )
    user_message = "用户问题：\n" + request.user_message

    return [{"role": "system", "content": system_message}, {"role": "user", "content": user_message}]

class CustomServiceAgent:
    def __init__(
        self,
        *,
        chat_http_client: httpx.Client | None = None,
        chat_api_key: str | None = None,
        chat_base_url: str | None = None,
        chat_model_name: str | None = None,
    ) -> None:
        """初始化第 02 课 Agent，并允许测试注入模型 HTTP 客户端。"""

        # 这是最小会话状态，用来证明同一个 session_id 下的请求会被归到同一段对话。
        self._message_count_by_session: dict[str, int] = {}
        self._chat_http_client = chat_http_client
        self._chat_api_key = chat_api_key
        self._chat_base_url = chat_base_url
        self._chat_model_name = chat_model_name
    @observe_chat
    def chat(self, request) -> ChatResponse:
        """处理最小聊天请求，证明 `/chat` 已能承接用户消息和系统事实。"""

        self._message_count_by_session[request.session_id] = self._message_count_by_session.get(
            request.session_id, 0) + 1
        message_count = self._message_count_by_session[request.session_id]

        messages = build_customer_msssage(request)

        log_course_event("PROMPT_BOUNDARY_READY", "客服Prompt边界已装配", teaching=True, message_count=len(messages), business_tools=False)

        answer = call_chat_model(
            messages,
            http_client=self._chat_http_client,
            api_key=self._chat_api_key,
            base_url=self._chat_base_url,
            model=self._chat_model_name,
        )
        log_course_event("LLM_ONLY_ANSWER_READY", "纯模型客服回答已生成", teaching=True, answer_source="llm_only", answer_length=len(answer))
        reasoning_summary = [
            "后端接收 ChatRequest，并把用户问题包装成第一版客服 messages。",
            "模型会生成自然语言客服回答，但当前版本没有活动、订单、物流或退款事实来源。",
            "从 ReAct 缺口看，这一版还没有真正的 Action 和 Observation。",
            "这一版响应不能被业务系统当成处理结果。",
        ]

        session_state = {
            "agent_version": "lesson-02-chat-service",
            "message_count": message_count,
            "runtime_context": {
                # 调试后台用这里验证：系统侧用户事实已经被 Agent 接住。
                "user_id": request.runtime_user_id,
                "nickname": request.runtime_nickname,
                "member_level": request.runtime_member_level,
                "risk_level": request.runtime_risk_level,
                "page_context": request.runtime_context or {},
            },
            "llm_customer_boundary": {
                "answer_source": "llm_only",
                "promotion_rules": "not_connected",
                "order_logistics": "not_connected",
                "refund_policy": "not_connected",
                "business_tools": "not_connected",
            },
            "next_gap": "能聊天不代表能接客服；真实业务问题很快会暴露第一版 AI 客服的缺口。",
        }
        return  ChatResponse(
            session_id=request.session_id,
            answer=answer,
            reasoning_summary=reasoning_summary,
            session_state=session_state)

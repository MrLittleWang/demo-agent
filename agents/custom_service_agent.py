from agent_logging import log_course_event, observe_chat
from api.schemas import ChatResponse
from models.llm_client import call_chat_model


class CustomServiceAgent:
    def __init__(
        self
    ) -> None:
        """初始化第 02 课 Agent，并允许测试注入模型 HTTP 客户端。"""

        # 这是最小会话状态，用来证明同一个 session_id 下的请求会被归到同一段对话。
        self._message_count_by_session: dict[str, int] = {}
    @observe_chat
    def chat(self, request) -> ChatResponse:
        """处理最小聊天请求，证明 `/chat` 已能承接用户消息和系统事实。"""

        self._message_count_by_session[request.session_id] = self._message_count_by_session.get(
            request.session_id, 0) + 1
        message_count = self._message_count_by_session[request.session_id]
        log_course_event("SESSION_MESSAGE_COUNTED", "会话消息计数完成", teaching=True, message_count=message_count)
        answer = call_chat_model(request.user_message,
                                 request.session_id)
        log_course_event("CHAT_ANSWER_READY", "模型回答已生成", answer_length=len(answer))
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
            "next_gap": "能聊天不代表能接客服；真实业务问题很快会暴露第一版 AI 客服的缺口。",
        }
        return  ChatResponse(
            session_id=request.session_id,
            answer=answer,
            session_state=session_state)

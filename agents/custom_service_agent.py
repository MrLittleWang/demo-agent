from agent_logging import observe_chat
from api.schemas import ChatResponse
from models.llm_client import call_chat_model


class CustomServiceAgent:

    @observe_chat
    def chat(self, chat_request) -> ChatResponse:
        """处理最小聊天请求，证明 `/chat` 已能承接用户消息和系统事实。"""
        answer = call_chat_model(chat_request.user_message,
                                 chat_request.session_id)
        return ChatResponse(answer=answer, session_id=chat_request.session_id)

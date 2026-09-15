
from api.schemas import ChatResponse
from models.llm_client import call_chat_model



class CustomServiceAgent:

        
    def chat(self, chat_request) -> ChatResponse:

        answer = call_chat_model(chat_request.user_message, chat_request.session_id)
        return ChatResponse(answer=answer, session_id=chat_request.session_id)

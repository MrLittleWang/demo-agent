

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_message: str = Field(..., description="用戶输入的问题")
    session_id: str = Field(..., description="会话ID，用于区分不同用户的对话历史")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="智能助手的回答")
    session_id: str = Field(..., description="会话ID，用于区分不同用户的对话历史")
    
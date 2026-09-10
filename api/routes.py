from typing import Any

from fastapi import APIRouter, HTTPException

from api.schemas import ChatRequest, ChatResponse


def creat_router(agent_provider: Any) -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    def health_check():
        return {"status": "ok"}

    @router.post("/chat")
    def chat(chat_request: ChatRequest) -> ChatResponse:
        try:
            return agent_provider.message.create(chat_request)
        except RuntimeError as e:
            raise HTTPException(status_code=503, detail=str(e)) from e

    return router
            